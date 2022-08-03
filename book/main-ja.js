// there must be a semicolon at the end of every line
export function main() {
   let actionList = document.querySelectorAll('.fpm');
   let promptList = document.querySelectorAll('div:nth-child(2) > div:nth-child(1) > p:nth-child(2):not(.iziModal-header-subtitle)');
   document.querySelector('.login-select > p').textContent = "ダンプするアカウントを選択してください。";
   document.querySelector('.login-select > h2').textContent = "マイページダンパー";
   document.querySelector('.bottom_btn > ul > li > a').textContent = "キャンセル";
   const style = document.createElement('style');
   style.textContent = ".user-info__detail__lv, .user-info__detail__lv::after, .btn_pink { background: #4A004F !important; } .user-info__detail__name { color: red !important; }";
   document.head.append(style);

   for (const actionKey of actionList) {
      actionKey.action = "https://w.yello.ooo/api/scrape/ja";
      actionKey.querySelector("\x23\x61\x69\x6d\x65\x49\x64").name = "userId";
   }

   for (const promptKey of promptList) {
       promptKey.innerHTML = "<b>プレーヤーデータをダンプしますか？</b>";
   }

   return;
}
