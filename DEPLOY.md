# 배포 가이드 — Streamlit Community Cloud

발표장 PC에 Python이 없어도 브라우저에서 URL만 열면 되도록, 무료 Streamlit
Community Cloud에 올리는 방법입니다.

## 1. GitHub에 올리기

1. GitHub에서 새 저장소 생성 (예: `navi-demo`)
   - **Public**: 링크만 있으면 누구나 접속 가능 (발표장에서 로그인 불필요)
   - **Private**: 초대한 사람만 접속 가능 (발표장 PC에서 로그인 필요)
2. 이 폴더(`navi/`) 안의 내용 전체를 저장소 루트에 올립니다.
   `demo_data/` 폴더가 꼭 포함되어야 합니다.

```bash
cd navi
git init
git add .
git commit -m "navi demo"
git branch -M main
git remote add origin https://github.com/<계정>/navi-demo.git
git push -u origin main
```

> 웹에서 올릴 경우: 저장소 화면 → **Add file → Upload files** → 폴더 내용을 드래그.
> `.streamlit`처럼 점(.)으로 시작하는 폴더는 드래그로 안 올라갈 수 있으니 확인하세요.
> (없어도 실행에는 문제 없음)

## 2. Streamlit Community Cloud 배포

1. https://share.streamlit.io 접속 → GitHub 계정으로 로그인
2. **Create app** → **Deploy a public app from GitHub**
3. 입력값
   - Repository: `<계정>/navi-demo`
   - Branch: `main`
   - Main file path: `dashboard.py`
   - App URL: 원하는 주소 (예: `navi-demo`)
4. **Advanced settings** → Python version **3.12** 선택
5. **Deploy** → 2~3분 뒤 `https://<주소>.streamlit.app` 생성

`.env`나 Secrets 설정은 필요 없습니다. 코드 기본값이 `demo_data/`를 가리킵니다.

## 3. 발표 당일 체크

- 일정 시간 접속이 없으면 앱이 잠듭니다. **발표 10분 전 한 번 열어서 깨워두세요.**
  ("Yo, this app has gone to sleep" 화면이 나오면 버튼을 누르고 30초~1분 대기)
- 발표장 네트워크가 불안정할 수 있으니 시연 화면 녹화본을 백업으로 준비하세요.
- 앱 화면에서 작성한 분석 노트는 서버에 임시 저장되며, 앱이 재시작되면 사라집니다.

## 4. 수정 후 반영

GitHub에 push하면 자동으로 다시 배포됩니다.
