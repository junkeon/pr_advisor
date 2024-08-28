import copy
import json
import os

import requests
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_upstage import ChatUpstage

load_dotenv()


class PR_Advisor:
    def __init__(self):
        REPO_OWNER = os.getenv("REPO_OWNER")
        REPO_NAME = os.getenv("REPO_NAME")
        GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
        UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

        self.url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        self.headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
        }

        self.chat = ChatUpstage(api_key=UPSTAGE_API_KEY)
        self.history = self.load_history(os.getenv("HISTORY_FILE_PATH"))

    def load_history(self, history_file_path):
        # history : {pr_number: pr_title}
        if os.path.exists(history_file_path):
            with open(history_file_path, "r") as file:
                history = json.load(file)
        else:
            history = {}

        return history

    def get_pr_list(self):
        headers = copy.deepcopy(self.headers)
        headers["Accept"] = "application/vnd.github+json"

        response = requests.get(
            f"{self.url}/pulls", headers=headers, params={"state": "open"}
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get pr list: {response.status_code}")

        prs_res = response.json()

        pr_list = []
        for pr in prs_res:
            pr_list.append(pr["number"])

        return pr_list

    def get_pr_info(self, pr_number):
        headers = copy.deepcopy(self.headers)
        headers["Accept"] = "application/vnd.github+json"

        response = requests.get(f"{self.url}/pulls/{pr_number}", headers=headers)

        if response.status_code != 200:
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

        if response.status_code != 200:
            raise Exception(f"Failed to get pr diff: {response.status_code}")

        diff_res = response.json()

        if len(diff_res) == 0:
            raise Exception("No diff found")
        if len(diff_res) > 100:
            raise Exception("Too many diffs")

        total_diff = ""
        for diff in diff_res:
            if diff.get("patch"):
                total_diff += f"{diff['filename']} : {diff['patch']}\n"

        return total_diff

    def get_llm_comment(self, pr_number):
        title, body, diff = self.get_pr_info(pr_number)

        messages = [
            SystemMessage(
                content="You are an experienced software engineer with a strong ability to provide valuable feedback on code improvements. \
                    Please review the PR and provide a detailed comment in Korean, following these guidelines:\
                    PR 요약: 이 PR의 목표와 주요 변경 사항을 명확하게 요약해 주세요. \
                    코드 가독성 및 유지보수성: 코드가 이해하기 쉽고 명확하게 작성되었는지 평가해 주세요. 변수명, 함수명, 주석이 적절한지, 그리고 코드 구조가 유지보수에 용이하게 작성되었는지 언급해 주세요. \
                    기능적 정확성 및 테스트: 코드가 예상대로 동작할 가능성이 있는지 평가하고, 필요한 테스트가 충분히 포함되었는지, 추가로 필요한 테스트가 있는지 설명해 주세요. \
                    성능 고려사항: 코드가 성능에 어떤 영향을 미칠지 평가해 주세요. 성능 저하의 가능성이 있거나 최적화가 필요한 부분이 있는지 언급해 주세요. \
                    보안 검토: 코드에 보안 취약점이 없는지 확인해 주세요. 특히, 토큰, 인증키 등이 포함되지는 않는지 확인해주세요. \
                    리뷰 중점 사항 : 다른 사람들이 집중해서 확인해야 하는 사항을 언급해주세요. \
                    건설적인 피드백 제공: 코드의 장점을 칭찬하고, 개선이 필요한 부분에 대해 건설적인 제안을 제공해 주세요. 필요한 경우, 더 나은 방법을 제시할 수 있는 질문을 추가해 주세요. \
                    위 지침에 따라 간결하고 명확한 코멘트를 작성해 주세요.",
            ),
            HumanMessage(
                content=f"PR title: {title}\nPR body: {body}\nPR diff: {diff}"
            ),
        ]

        response = self.chat.invoke(messages)

        return response.content

    def create_comment(self, pr_number, comment):
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

        return "Success create comment"
