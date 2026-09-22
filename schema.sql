-- =========================================================
-- "한 줄, 두 권" Supabase 테이블 생성 SQL  (ERD 그대로)
-- =========================================================
-- 사용법
--   Supabase 대시보드 > SQL Editor 에 붙여넣고 [Run] 실행
--
-- 참고
--   이 프로젝트는 SUPABASE_SERVICE_ROLE_KEY(서버 전용 키)로
--   접속하므로 RLS(행 수준 보안)를 켜지 않아도 동작한다.
--   실제 서비스로 확장할 때는 RLS 정책을 별도로 설계할 것.
-- =========================================================


-- ---------------------------------------------------------
-- 1) users : 회원
-- ---------------------------------------------------------
create table if not exists users (
    id            bigint generated always as identity primary key,
    login_id      varchar not null unique,
    password_hash varchar not null,
    created_at    timestamptz not null default now()
);


-- ---------------------------------------------------------
-- 2) diaries : 한 줄 일기 (AI 분석 결과 포함)
-- ---------------------------------------------------------
create table if not exists diaries (
    id                  bigint generated always as identity primary key,
    user_id             bigint not null
                        references users(id) on delete cascade,
    content             varchar not null,
    emotion             varchar,
    topic               varchar,
    viewpoint           text,
    support_keyword     varchar,
    perspective_keyword varchar,
    created_at          timestamptz not null default now(),
    updated_at          timestamptz not null default now()
);


-- ---------------------------------------------------------
-- 3) books : 카카오에서 찾은 책 정보 (ISBN 기준 중복 방지)
-- ---------------------------------------------------------
create table if not exists books (
    id         bigint generated always as identity primary key,
    isbn       varchar unique,
    title      varchar,
    authors    text[],
    publisher  varchar,
    thumbnail  text,
    contents   text,
    book_url   text,
    created_at timestamptz not null default now()
);


-- ---------------------------------------------------------
-- 4) recommendations : 일기별 추천 기록
--    recommendation_type : 'support'(공감) / 'opposite'(다른 관점)
-- ---------------------------------------------------------
create table if not exists recommendations (
    id                  bigint generated always as identity primary key,
    diary_id            bigint not null
                        references diaries(id) on delete cascade,
    book_id             bigint not null
                        references books(id) on delete cascade,
    recommendation_type varchar not null,
    reason              text,
    created_at          timestamptz not null default now()
);


-- ---------------------------------------------------------
-- 5) connection_test : 연결 테스트용 (선택)
-- ---------------------------------------------------------
create table if not exists connection_test (
    id         bigint generated always as identity primary key,
    message    text,
    created_at timestamptz default now()
);


-- ---------------------------------------------------------
-- 조회 속도를 위한 인덱스
-- ---------------------------------------------------------
create index if not exists idx_diaries_user_id
    on diaries(user_id);

create index if not exists idx_recommendations_diary_id
    on recommendations(diary_id);
