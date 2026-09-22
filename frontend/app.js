// =========================================================
// 한 줄, 두 권 - 프론트엔드 로직 (순수 자바스크립트)
// =========================================================
//
// 흐름
//   1) 회원가입 / 로그인 → JWT 토큰을 브라우저에 저장
//   2) 한 줄 일기 작성 → 서버가 AI 분석 후 저장
//   3) 추천받기 → 카카오 도서 API로 책 두 권 추천 & 저장
//   4) 지난 일기 목록 확인 / 다시 추천 / 삭제
// =========================================================

// API 서버 주소 (프론트와 같은 서버에서 제공되므로 상대경로 사용)
const API = "";

// 브라우저에 저장된 JWT 토큰 (localStorage)
let token = localStorage.getItem("token") || "";


// ---------------------------------------------------------
// 화면 요소 가져오기
// ---------------------------------------------------------
const authSection = document.getElementById("auth-section");
const appSection = document.getElementById("app-section");

const tabLogin = document.getElementById("tab-login");
const tabSignup = document.getElementById("tab-signup");
const authSubmit = document.getElementById("auth-submit");
const authMessage = document.getElementById("auth-message");

const inputLoginId = document.getElementById("login-id");
const inputPassword = document.getElementById("password");

const welcome = document.getElementById("welcome");
const logoutBtn = document.getElementById("logout");

const diaryContent = document.getElementById("diary-content");
const diarySubmit = document.getElementById("diary-submit");
const diaryMessage = document.getElementById("diary-message");
const recommendResult = document.getElementById("recommend-result");
const diaryList = document.getElementById("diary-list");


// 현재 탭 상태 ("login" 또는 "signup")
let mode = "login";


// ---------------------------------------------------------
// 공통 함수: 서버에 요청 보내기 (JWT 자동 첨부)
// ---------------------------------------------------------
async function callApi(path, method = "GET", body = null) {
  const options = {
    method,
    headers: { "Content-Type": "application/json" }
  };

  // 로그인 상태면 Authorization 헤더에 토큰 첨부
  if (token) {
    options.headers["Authorization"] = "Bearer " + token;
  }

  // 보낼 데이터가 있으면 JSON으로 변환
  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(API + path, options);
  const data = await response.json();

  // 오류 응답이면 예외 발생
  if (!response.ok) {
    throw new Error(data.detail || "요청 실패");
  }

  return data;
}


// ---------------------------------------------------------
// 탭 전환 (로그인 <-> 회원가입)
// ---------------------------------------------------------
tabLogin.addEventListener("click", () => {
  mode = "login";
  tabLogin.classList.add("active");
  tabSignup.classList.remove("active");
  authSubmit.textContent = "로그인";
  authMessage.textContent = "";
});

tabSignup.addEventListener("click", () => {
  mode = "signup";
  tabSignup.classList.add("active");
  tabLogin.classList.remove("active");
  authSubmit.textContent = "회원가입";
  authMessage.textContent = "";
});


// ---------------------------------------------------------
// 로그인 / 회원가입 버튼
// ---------------------------------------------------------
authSubmit.addEventListener("click", async () => {
  const loginId = inputLoginId.value.trim();
  const password = inputPassword.value.trim();

  authMessage.className = "message";

  if (loginId.length < 4 || password.length < 4) {
    authMessage.textContent =
      "아이디와 비밀번호는 4자 이상이어야 합니다.";
    return;
  }

  try {
    if (mode === "signup") {
      // 회원가입 요청
      await callApi("/auth/signup", "POST", {
        login_id: loginId,
        password: password
      });

      // 먼저 로그인 탭으로 이동한 뒤 (탭 전환은 메시지를 지우므로)
      tabLogin.click();

      // 성공 메시지를 남긴다 (탭 전환 후에 넣어야 화면에 유지됨)
      authMessage.className = "message success";
      authMessage.textContent =
        "회원가입 완료! 이제 로그인해 주세요.";

      // 방금 입력한 아이디를 그대로 두어 바로 로그인하기 편하게
      inputPassword.value = "";
      inputPassword.focus();
    } else {
      // 로그인 요청
      const data = await callApi("/auth/login", "POST", {
        login_id: loginId,
        password: password
      });

      // 토큰 저장
      token = data.access_token;
      localStorage.setItem("token", token);
      localStorage.setItem("loginId", data.user.login_id);

      // 서비스 화면으로 전환
      showApp();
    }
  } catch (error) {
    authMessage.className = "message";
    authMessage.textContent = error.message;
  }
});


// ---------------------------------------------------------
// 로그아웃
// ---------------------------------------------------------
logoutBtn.addEventListener("click", () => {
  token = "";
  localStorage.removeItem("token");
  localStorage.removeItem("loginId");
  showAuth();
});


// ---------------------------------------------------------
// 한 줄 일기 작성 + 바로 추천받기
// ---------------------------------------------------------
diarySubmit.addEventListener("click", async () => {
  const content = diaryContent.value.trim();
  diaryMessage.className = "message";

  if (content.length < 1) {
    diaryMessage.textContent = "한 줄을 입력해 주세요.";
    return;
  }

  try {
    diarySubmit.disabled = true;
    diaryMessage.className = "message success";
    diaryMessage.textContent =
      "AI가 문장을 분석하고 책을 찾고 있어요...";

    // 1) 일기 등록 (서버에서 AI 분석 후 저장)
    const created = await callApi("/diaries", "POST", {
      content: content
    });
    const diaryId = created.diary.id;

    // 2) 추천 생성 (책 두 권 추천 & 저장)
    const result = await callApi("/recommendations", "POST", {
      diary_id: diaryId
    });

    // 3) 추천 결과 화면에 표시
    renderRecommendations(result.recommendations);

    diaryMessage.textContent = "추천 완료!";
    diaryContent.value = "";

    // 4) 지난 일기 목록 새로고침
    loadDiaries();
  } catch (error) {
    diaryMessage.className = "message";
    diaryMessage.textContent = error.message;
  } finally {
    diarySubmit.disabled = false;
  }
});


// ---------------------------------------------------------
// 추천 결과(책 카드) 그리기
// ---------------------------------------------------------
function renderRecommendations(recommendations) {
  recommendResult.innerHTML = "";

  recommendations.forEach((rec) => {
    // 서버 응답에는 book 정보가 들어 있음
    // (추천 생성 응답: rec.book / 조회 응답: rec.books)
    const book = rec.book || rec.books || {};
    const isSupport = rec.recommendation_type === "support";

    const badgeClass = isSupport
      ? "badge-support"
      : "badge-opposite";
    const badgeText = isSupport
      ? "🤍 공감 관점"
      : "🔄 다른 관점";

    // 저자 배열 → 문자열
    const authors = Array.isArray(book.authors)
      ? book.authors.join(", ")
      : "";

    const card = document.createElement("div");
    card.className = "book-card";
    card.innerHTML = `
      <span class="book-badge ${badgeClass}">${badgeText}</span>
      <img
        class="book-thumb"
        src="${book.thumbnail || ""}"
        alt="표지"
        onerror="this.style.display='none'"
      />
      <div class="book-title">${book.title || "제목 없음"}</div>
      <div class="book-author">${authors}</div>
      <div class="book-reason">${rec.reason || ""}</div>
    `;
    recommendResult.appendChild(card);
  });
}


// ---------------------------------------------------------
// 지난 일기 목록 불러오기
// ---------------------------------------------------------
async function loadDiaries() {
  try {
    const data = await callApi("/diaries");
    diaryList.innerHTML = "";

    if (data.diaries.length === 0) {
      diaryList.innerHTML =
        "<p style='color:#a99e8f'>아직 남긴 한 줄이 없어요.</p>";
      return;
    }

    data.diaries.forEach((diary) => {
      const item = document.createElement("div");
      item.className = "diary-item";

      // 날짜를 보기 좋게 (앞 10글자: YYYY-MM-DD)
      const date = (diary.created_at || "").substring(0, 10);

      item.innerHTML = `
        <div class="diary-text">${diary.content}</div>
        <div class="diary-meta">
          ${date}
          ${diary.emotion ? " · " + diary.emotion : ""}
          ${diary.topic ? " · " + diary.topic : ""}
        </div>
        <div class="diary-actions">
          <button data-id="${diary.id}" class="btn-recommend">
            다시 추천
          </button>
          <button data-id="${diary.id}" class="btn-delete">
            삭제
          </button>
        </div>
      `;
      diaryList.appendChild(item);
    });

    // "다시 추천" 버튼 연결
    document.querySelectorAll(".btn-recommend").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = Number(btn.getAttribute("data-id"));
        try {
          const result = await callApi(
            "/recommendations",
            "POST",
            { diary_id: id }
          );
          renderRecommendations(result.recommendations);
          window.scrollTo({ top: 0, behavior: "smooth" });
        } catch (error) {
          alert(error.message);
        }
      });
    });

    // "삭제" 버튼 연결
    document.querySelectorAll(".btn-delete").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = Number(btn.getAttribute("data-id"));
        try {
          await callApi("/diaries/" + id, "DELETE");
          loadDiaries();
        } catch (error) {
          alert(error.message);
        }
      });
    });
  } catch (error) {
    // 토큰이 만료되면 다시 로그인 화면으로
    diaryList.innerHTML = "";
    showAuth();
  }
}


// ---------------------------------------------------------
// 화면 전환 함수
// ---------------------------------------------------------
function showApp() {
  authSection.classList.add("hidden");
  appSection.classList.remove("hidden");
  welcome.textContent =
    (localStorage.getItem("loginId") || "") + "님, 반가워요 👋";
  recommendResult.innerHTML = "";
  loadDiaries();
}

function showAuth() {
  appSection.classList.add("hidden");
  authSection.classList.remove("hidden");
  inputLoginId.value = "";
  inputPassword.value = "";
}


// ---------------------------------------------------------
// 첫 실행: 저장된 토큰이 있으면 바로 서비스 화면
// ---------------------------------------------------------
if (token) {
  showApp();
} else {
  showAuth();
}
