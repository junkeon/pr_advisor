import copy
import json
import os
import time
from datetime import datetime

import requests
from dotenv import load_dotenv
from langchain_upstage import ChatUpstage

from response_schema import output_parser, prompt

load_dotenv()

TIME_SLEEP = 60 * 10  # 10 minutes


class PR_Advisor:
    def __init__(self):
        REPO_OWNER = os.getenv("REPO_OWNER")
        REPO_NAME = os.getenv("REPO_NAME")
        GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
        UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
        self.history_file_path = os.getenv("HISTORY_FILE_PATH")

        self.url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        self.headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
        }

        self.chat = ChatUpstage(api_key=UPSTAGE_API_KEY)
        self.history = self.load_history(self.history_file_path)

    def load_history(self, history_file_path):
        # history : {pr_number: pr_title}
        if os.path.exists(history_file_path):
            with open(history_file_path, "r") as file:
                history = json.load(file)
            print("> Success to load history")
        else:
            history = {}
            print("> No history file")

        return history

    def get_pr_list(self):
        headers = copy.deepcopy(self.headers)
        headers["Accept"] = "application/vnd.github+json"

        response = requests.get(
            f"{self.url}/pulls", headers=headers, params={"state": "open"}
        )

        if response.status_code == 200:
            print("> Success to get pr list")
        elif response.status_code == 404:
            raise Exception(f"Failed to get pr list: {response.status_code}")
        else:
            raise Exception(f"Failed to get pr list: {response.status_code}")

        prs_res = response.json()

        pr_list = []
        for pr in prs_res:
            pr_list.append((pr["number"], pr["title"]))

        return pr_list

    def get_pr_info(self, pr_number):
        headers = copy.deepcopy(self.headers)
        headers["Accept"] = "application/vnd.github+json"

        response = requests.get(f"{self.url}/pulls/{pr_number}", headers=headers)

        if response.status_code == 200:
            print("> Success to get pr info")
        elif response.status_code == 404:
            raise Exception(f"PR {pr_number} is not found")
        else:
            raise Exception(f"Failed to get pr info: {response.status_code}")

        pr_res = response.json()

        title = pr_res["title"]
        body = pr_res["body"]
        diff = self.get_pr_diff(pr_number)

        return title, body, diff

    def get_pr_diff(self, pr_number):
        headers = copy.deepcopy(self.headers)
        headers["Accept"] = "application/vnd.github.diff"
        response = requests.get(f"{self.url}/pulls/{pr_number}/files", headers=headers)

        if response.status_code == 200:
            print("> Success to get pr diff")
        elif response.status_code == 404:
            raise Exception(f"PR {pr_number} is not found")
        else:
            raise Exception(f"Failed to get pr diff: {response.status_code}")

        diff_res = response.json()

        if len(diff_res) == 0:
            raise Exception("No diff found")
        if len(diff_res) > 100:
            raise Exception("Too many diffs")

        print(f"> Number of diffs: {len(diff_res)}")

        total_diff = ""
        for diff in diff_res:
            if diff.get("patch"):
                total_diff += f"{diff['filename']} : {diff['patch']}\n"

        return total_diff

    def get_llm_comment(self, pr_number):
        title, body, diff = self.get_pr_info(pr_number)

        if "Bump" in title:
            raise Exception("Bump PR")

        chain = prompt | self.chat | output_parser

        response = chain.invoke({"title": title, "body": body, "diff": diff})

        str_response = "Automated Review Comment by Solar:\n\n"
        for key, value in response.items():
            str_response += f"- {key.replace('_', ' ').capitalize()}: {value}\n"

        return str_response.strip()

    def create_comment(self, pr_number, comment, just_print=False):
        if just_print:
            print(comment)
            return

        headers = copy.deepcopy(self.headers)
        headers["Accept"] = "application/vnd.github+json"

        comment_body = {"body": f"Automated Review Comment:\n\n{comment}"}

        response = requests.post(
            f"{self.url}/issues/{pr_number}/comments",
            headers=headers,
            json=comment_body,
        )

        if response.status_code != 201:
            raise Exception(f"Failed to create comment: {response.status_code}")

        print("> Success create comment")

    def save_history(self):
        with open(self.history_file_path, "w") as file:
            json.dump(self.history, file, indent=4, ensure_ascii=False)

        print("> Success save history")

    def run(self):
        pr_list = self.get_pr_list()
        print(f"> Number of open PRs: {len(pr_list)}")

        nothing_to_review = True

        for pr_number, title in pr_list:
            if str(pr_number) not in self.history:
                nothing_to_review = False
                print(f"> PR {pr_number} [{title}] is not in history")

                try:
                    comment = self.get_llm_comment(pr_number)
                    self.create_comment(pr_number, comment, True)

                except Exception as e:
                    print(e)

                finally:
                    self.history[str(pr_number)] = title
                    self.save_history()
                    print()
                    time.sleep(10)

        if nothing_to_review:
            print("> Nothing to review")

    def run_periodically(self):
        while True:
            print()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Start running")
            self.run()
            time.sleep(TIME_SLEEP)


if __name__ == "__main__":
    pr_advisor = PR_Advisor()
    pr_advisor.run_periodically()
