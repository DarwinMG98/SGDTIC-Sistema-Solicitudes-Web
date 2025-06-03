
  const stepMenuOne = document.querySelector('.formbold-step-menu1')
  const stepMenuTwo = document.querySelector('.formbold-step-menu2')
  const stepMenuThree = document.querySelector('.formbold-step-menu3')

  const stepOne = document.querySelector('.formbold-form-step-1')
  const stepTwo = document.querySelector('.formbold-form-step-2')
  const stepThree = document.querySelector('.formbold-form-step-3')

  const formSubmitBtn = document.querySelector('.formbold-btn')
  const formBackBtn = document.querySelector('.formbold-back-btn')

  const fileInput = document.getElementById('fileInput');
  const fileList = document.getElementById('fileList');
  let selectedFiles = [];

fileInput.addEventListener('change', function(event) {
  selectedFiles = Array.from(fileInput.files);
  renderFileList();
});


function renderFileList() {
  fileList.innerHTML = '';
  selectedFiles.forEach((file, idx) => {
    const li = document.createElement('li');
    li.textContent = file.name + ' ';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = 'Quitar';
    btn.style.marginLeft = '1rem';
    btn.onclick = function() {
      selectedFiles.splice(idx, 1);
      renderFileList();
      // Actualiza input
      updateFileInput();
    };
    li.appendChild(btn);
    fileList.appendChild(li);
  });
}

function updateFileInput() {
  const dataTransfer = new DataTransfer();
  selectedFiles.forEach(f => dataTransfer.items.add(f));
  fileInput.files = dataTransfer.files;
}

  formSubmitBtn.addEventListener("click", function(event){
    event.preventDefault()
    if(stepMenuOne.className == 'formbold-step-menu1 active') {
        event.preventDefault()

        stepMenuOne.classList.remove('active')
        stepMenuTwo.classList.add('active')

        stepOne.classList.remove('active')
        stepTwo.classList.add('active')

        formBackBtn.classList.add('active')
        formBackBtn.addEventListener("click", function (event) {
          event.preventDefault()

          stepMenuOne.classList.add('active')
          stepMenuTwo.classList.remove('active')

          stepOne.classList.add('active')
          stepTwo.classList.remove('active')

          formBackBtn.classList.remove('active')

        })

      } else if(stepMenuTwo.className == 'formbold-step-menu2 active') {
        event.preventDefault()

        stepMenuTwo.classList.remove('active')
        stepMenuThree.classList.add('active')

        stepTwo.classList.remove('active')
        stepThree.classList.add('active')

        formBackBtn.classList.remove('active')
        formSubmitBtn.textContent = 'Submit'
      } else if(stepMenuThree.className == 'formbold-step-menu3 active') {
        document.querySelector('form').submit()
      }
  })

function toggleSOVersion() {
  const so = document.getElementById('soSelect').value;
  document.getElementById('windowsVersion').style.display = so === 'Windows Server' ? 'block' : 'none';
  document.getElementById('linuxVersion').style.display = so === 'Linux' ? 'block' : 'none';
  document.getElementById('otroSO').style.display = so === 'Otro' ? 'block' : 'none';
}



