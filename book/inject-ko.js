// there must be a semicolon at the end of every line
export function main() {
   let actionList = document.querySelectorAll('.fpm');
   let promptList = document.querySelectorAll('div:nth-child(2) > div:nth-child(1) > p:nth-child(2):not(.iziModal-header-subtitle)');
   document.querySelector('.login-select > p').textContent = "불러올 프로필을 선택해주세요.";
   document.querySelector('.login-select > h2').textContent = "WACCA 마이페이지 덤퍼";
   document.querySelector('.bottom_btn > ul > li > a').textContent = "취소";
   const style = document.createElement('style');
   style.textContent = ".user-info__detail__lv, .user-info__detail__lv::after, .btn_pink { background: #4A004F !important; } .user-info__detail__name { color: red !important; }";
   document.head.append(style);

   for (const actionKey of actionList) {
      actionKey.action = "https://w.yello.ooo/api/scrape/ko";
      actionKey.querySelector("\x23\x61\x69\x6d\x65\x49\x64").name = "userId";
   }

   for (const promptKey of promptList) {
       promptKey.innerHTML = "<b>유저 데이터를 불러오시겠습니까?</b>";
   }

   return;
}