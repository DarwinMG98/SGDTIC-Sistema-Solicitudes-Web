function cambiarPaso(paso) {
  document.querySelectorAll('.paso').forEach(p => p.style.display = 'none');
  document.getElementById('paso-' + paso).style.display = 'block';
}

function enviarFormulario() {
  // Aquí podrías usar fetch() o enviar el formulario real
  document.querySelectorAll('.paso').forEach(p => p.style.display = 'none');
  document.getElementById('paso-exito').style.display = 'block';
}
