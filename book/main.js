// there must be a semicolon at the end of every line
let actionList = document.querySelectorAll('.fpm');
let promptList = document.querySelectorAll('div:nth-child(2) > div:nth-child(1) > p:nth-child(2):not(.iziModal-header-subtitle)');
document.querySelector('.login-select > p').textContent = "Select a profile to dump:";
document.querySelector('.login-select > h2').textContent = "WACCA (MyPage Dump)";
document.querySelector('.bottom_btn > ul > li > a').textContent = "Cancel";

for (const actionKey of actionList) {
   actionKey.action = "http://localhost:8000/api/scrape";
   actionKey.querySelector("\x23\x61\x69\x6d\x65\x49\x64").name = "userId";
   actionKey.querySelector('.btn_pink').style.backgroundColor = '#4A004F';
}

for (const promptKey of promptList) {
    promptKey.innerHTML = "<b>Dump user data?</b>";
}