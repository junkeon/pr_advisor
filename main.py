import copy
import json
import logging
import os
import time

import requests
from dotenv import load_dotenv

from response_schema import LLMAdvisor

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] (%(levelname)s) : %(message)s",
    handlers=[logging.FileHandler("pr_advisor.log"), logging.StreamHandler()],
)


class PR_Advisor:
    def __init__(self):
        REPO_OWNER = os.getenv("REPO_OWNER")
        REPO_NAME = os.getenv("REPO_NAME")
        GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
        LLM_API_KEY = os.getenv("LLM_API_KEY")
        self.history_file_path = os.getenv("HISTORY_FILE_PATH")

        self.url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        self.headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
        }
        self.llm_model = "Solar"
        self.llm_advisor = LLMAdvisor(model=self.llm_model, api_key=LLM_API_KEY)
        self.history = self.load_history(self.history_file_path)

    def load_history(self, history_file_path):
        # history : {pr_number: pr_title}
        if os.path.exists(history_file_path):
            with open(history_file_path, "r") as file:
                history = json.load(file)
            logging.info("Success to load history")
        else:
            history = {}
            logging.info("No history file")

        return history

    def get_pr_list(self):
        headers = copy.deepcopy(self.headers)
        headers["Accept"] = "application/vnd.github+json"

        response = requests.get(
            f"{self.url}/pulls", headers=headers, params={"state": "open"}
        )

        if response.status_code == 200:
            logging.info("Success to get pr list")
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
            logging.info("Success to get pr info")
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
            logging.info("Success to get pr diff")
        elif response.status_code == 404:
            raise Exception(f"PR {pr_number} is not found")
        else:
            raise Exception(f"Failed to get pr diff: {response.status_code}")

        diff_res = response.json()

        if len(diff_res) == 0:
            raise Exception("No diff found")
        if len(diff_res) > 100:
            raise Exception("Too many diffs")

        logging.info(f"Number of diffs: {len(diff_res)}")

        total_diff = ""
        for diff in diff_res:
            if diff.get("patch"):
                total_diff += f"{diff['filename']} : {diff['patch']}\n"

        return total_diff

    def get_llm_comment(self, pr_number):
        title, body, diff = self.get_pr_info(pr_number)

        if "Bump" in title:
            raise Exception("Bump PR")

        comment = self.llm_advisor.get_response(
            {"title": title, "body": body, "diff": diff}
        )

        return comment

    def create_comment(self, pr_number, comment, just_print=False):
        if just_print:
            print(comment)
            return

        headers = copy.deepcopy(self.headers)
        headers["Accept"] = "application/vnd.github+json"

        comment_body = {
            "body": f"Automated Review Comment by {self.llm_model}:\n\n{comment}"
        }

        response = requests.post(
            f"{self.url}/issues/{pr_number}/comments",
            headers=headers,
            json=comment_body,
        )

        if response.status_code != 201:
            raise Exception(f"Failed to create comment: {response.status_code}")

        logging.info("Success create comment")

    def save_history(self):
        with open(self.history_file_path, "w") as file:
            json.dump(self.history, file, indent=4, ensure_ascii=False)

        logging.info("Success save history")

    def run(self):
        pr_list = self.get_pr_list()
        logging.info(f"Number of open PRs: {len(pr_list)}")
        print()

        nothing_to_review = True

        for pr_number, title in pr_list:
            if str(pr_number) not in self.history:
                nothing_to_review = False
                logging.info(f"PR {pr_number} [{title}] is not in history")

                try:
                    comment = self.get_llm_comment(pr_number)
                    self.create_comment(pr_number, comment)

                except Exception as e:
                    logging.error(e)

                finally:
                    self.history[str(pr_number)] = title
                    self.save_history()
                    print()
                    time.sleep(10)

        if nothing_to_review:
            logging.info("Nothing to review")
            print()

    def run_periodically(self):
        if os.getenv("TIME_SLEEP"):
            time_sleep_str = os.getenv("TIME_SLEEP")
            logging.info(f"Load TIME_SLEEP: {time_sleep_str}")
            if time_sleep_str.endswith("s"):
                time_sleep = int(time_sleep_str[:-1])
            elif time_sleep_str.endswith("m"):
                time_sleep = int(time_sleep_str[:-1]) * 60
            elif time_sleep_str.endswith("h"):
                time_sleep = int(time_sleep_str[:-1]) * 3600
            else:
                raise Exception("Invalid TIME_SLEEP")
        else:
            time_sleep = 60 * 10  # default 10 minutes
            logging.info(f"No TIME_SLEEP, use default {time_sleep} seconds")

        print()

        while True:
            self.run()
            time.sleep(time_sleep)


if __name__ == "__main__":
    pr_advisor = PR_Advisor()
    pr_advisor.run_periodically()
