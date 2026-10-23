const language = document.querySelector('#language');
const status = document.querySelector('#status');

document.querySelector('#start').addEventListener('click', () => {
  status.textContent = `Running (${language.value})`;
});
