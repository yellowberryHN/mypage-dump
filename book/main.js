// there must be a semicolon at the end of every line
let actionList = document.querySelectorAll('.fpm');
let promptList = document.querySelectorAll('div:nth-child(2) > div:nth-child(1) > p:nth-child(2):not(.iziModal-header-subtitle)');
document.querySelector('.login-select > p').textContent = "Select a profile to dump:";
document.querySelector('.login-select > h2').textContent = "WACCA (MyPage Dump)" ;

for (const actionKey in actionList) {
   actionList[actionKey].action = "http://localhost:8000/api/scrape/";            
}

for (const promptKey of promptList) {
    promptKey.textContent = "Dump user data?"
}