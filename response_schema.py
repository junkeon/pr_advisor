from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_upstage import ChatUpstage


class LLMAdvisor:
    def __init__(self, model="Solar", api_key=None):

        if model == "Solar":
            self.chat = ChatUpstage(api_key=api_key, temperature=0)
        else:
            raise ValueError(f"{model} is not supported model")

        response_schemas = [
            ResponseSchema(
                name="summary",
                description="PR의 목적과 주요 변경 사항을 간단하고 명확하게 요약한 내용. PR이 해결하려는 문제와 변경이 코드베이스에 미치는 영향을 한국어로 작성하세요.",
            ),
            ResponseSchema(
                name="improvement_point",
                description="PR에서 코드 가독성, 유지보수성, 기능적 정확성, 성능, 보안, 코드 스타일 및 컨벤션 준수 등의 측면에서 개선이 필요한 부분을 한국어로 설명하세요.",
            ),
            ResponseSchema(
                name="security_point",
                description="PR에서 확인해야 할 보안 관련 사항을 한국어로 작성하세요. 특히 입력 검증, 인증 및 권한 관리, 데이터 암호화 등의 취약점이 없는지 평가하세요.",
            ),
            ResponseSchema(
                name="review_point",
                description="리뷰어가 중점적으로 확인해야 할 사항을 한국어로 작성하세요. 코드의 기능적 정확성, 가독성, 유지보수성, 성능, 보안, 테스트 커버리지 등의 측면에서 주의 깊게 봐야 할 부분을 강조하세요.",
            ),
        ]

        self.chain = self.set_chain(response_schemas)

    def set_chain(self, response_schemas):
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

        format_instructions = output_parser.get_format_instructions()
        prompt = PromptTemplate(
            template="You are an experienced software engineer with very kind and a strong ability to provide valuable feedback on code improvements. \
                Please review the PR and provide a detailed comment in Korean, following these guidelines:\n{format_instructions}\n{title}\n{body}\n{diff}",
            input_variables=["title", "body", "diff"],
            partial_variables={"format_instructions": format_instructions},
        )

        return prompt | self.chat | output_parser

    def generate_comment(self, body):
        response = self.chain.invoke(body)

        str_response = ""
        for key, value in response.items():
            str_response += f"- {key.replace('_', ' ').capitalize()}: {value}\n"

        return str_response.strip()
