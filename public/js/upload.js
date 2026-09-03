const input = document.getElementById('pdf');
input.onchange = () => {
  const form = new FormData();
  form.append('pdf', input.files[0]);

  const xhr = new XMLHttpRequest();
  xhr.upload.onprogress = e => {
    document.getElementById('progress').innerText = Math.round((e.loaded/e.total)*100) + '%';
  };
  xhr.open('POST', '/api/upload');
  xhr.send(form);
};
