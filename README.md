
# PR Advisor

PR Advisor는 GitHub Pull Request(PR)를 자동으로 리뷰하고, 코드 개선 사항을 제안하는 도구입니다. 이 도구는 PR의 목적, 주요 변경 사항, 개선이 필요한 부분, 보안 관련 사항 등을 한국어로 작성하여 리뷰어에게 제공합니다.

## 주요 기능

- GitHub PR 목록 가져오기
- PR 정보(제목, 본문, diff) 가져오기
- LLM을 사용하여 PR에 대한 자동 리뷰 생성
- GitHub에 자동으로 리뷰 코멘트 작성
- PR 리뷰 히스토리 관리

## 설치 및 실행

### 요구 사항

- Python 3.10
- Docker (선택 사항)

### 환경 변수 설정

`.env.example` 파일을 참고하여 `.env` 파일을 생성하고 다음과 같은 환경 변수를 설정합니다:

```env
REPO_OWNER=your_repo_owner
REPO_NAME=your_repo_name
GITHUB_TOKEN=your_github_token
LLM_API_KEY=your_upstage_api_key
HISTORY_FILE_PATH=path_to_history_file.json
TIME_SLEEP=10m  # 주기적으로 실행할 시간 간격 (예: 10분)
```

- `REPO_OWNER`: GitHub 저장소 소유자의 이름을 입력합니다.
- `REPO_NAME`: GitHub 저장소의 이름을 입력합니다.
- `GITHUB_TOKEN`: GitHub API에 접근하기 위한 개인 액세스 토큰을 입력합니다. 이 토큰은 해당 저장소의 PR에 대해 접근이 가능해야 합니다. ([참고](https://docs.github.com/ko/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-token))
- `LLM_API_KEY`: LLM API 키를 입력합니다. (현재는 [Upstage의 Solar](https://developers.upstage.ai/docs/getting-started/models#solar-llm)만 사용 가능)
- `HISTORY_FILE_PATH`: PR 리뷰 히스토리를 저장할 파일 경로를 입력합니다.
- `TIME_SLEEP`: 주기적으로 실행할 시간 간격을 설정합니다. 초(`s`), 분(`m`), 시간(`h`)

### 로컬에서 실행

1. 필요한 패키지를 설치합니다:

    ```bash
    pip install -r requirements.txt
    ```

2. 애플리케이션을 실행합니다:

    ```bash
    python main.py
    ```

### Docker에서 실행

1. Docker 이미지를 빌드합니다:

    ```bash
    docker build -t pr_advisor .
    ```

2. Docker 컨테이너를 실행합니다:

    ```bash
    docker run pr_advisor
    ```

## 파일 설명

### `response_schema.py`

LLMAdvisor 클래스를 정의하여 PR 리뷰를 위한 LLM 모델을 설정하고, PR 리뷰 코멘트를 생성합니다.

### `main.py`

PR_Advisor 클래스를 정의하여 GitHub PR 목록을 가져오고, PR 정보를 수집하며, LLM을 사용하여 자동 리뷰 코멘트를 생성하고, GitHub에 코멘트를 작성합니다.

### `requirements.txt`

필요한 Python 패키지를 나열합니다.

### `Dockerfile`

Docker 이미지를 빌드하기 위한 설정 파일입니다.

## 사용 예시

PR Advisor는 주기적으로 GitHub PR을 확인하고, 새로운 PR이 있을 경우 자동으로 리뷰 코멘트를 작성합니다. 주기적인 실행 간격은 `.env` 파일의 `TIME_SLEEP` 변수로 설정할 수 있습니다.

## 기여

기여를 원하시면, 이 저장소를 포크하고 풀 리퀘스트를 제출해 주세요. 버그 리포트나 기능 요청은 이슈 트래커를 통해 제출해 주세요.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.
