document.addEventListener('DOMContentLoaded', function () {
  // Inicializar tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.forEach(function (el) {
    new bootstrap.Tooltip(el, {
      trigger: 'hover', // solo al pasar el mouse
      placement: 'top'
    });
  });
});

$(document).ready(function () {
        $('#tablaIE').DataTable({
        language: {
            decimal: "",
            emptyTable: "No hay datos disponibles en la tabla",
            info: "Mostrando _START_ a _END_ de _TOTAL_ registros",
            infoEmpty: "Mostrando 0 a 0 de 0 registros",
            infoFiltered: "(filtrado de _MAX_ registros totales)",
            lengthMenu: "Mostrar _MENU_ registros",
            loadingRecords: "Cargando...",
            processing: "Procesando...",
            search: "Buscar:",
            zeroRecords: "No se encontraron resultados",
            paginate: {
            first: "Primero",
            last: "Último",
            next: "Siguiente",
            previous: "Anterior"
            },
            aria: {
            sortAscending: ": activar para ordenar ascendente",
            sortDescending: ": activar para ordenar descendente"
            }
        },
        pageLength: 10,
        lengthChange: false,
        ordering: false,
        info: true,
        responsive: true
        });
    });

$(document).ready(function() {
    $('#tablaExpedientes').DataTable({
        pageLength: 4, // solo 4 filas visibles al inicio
        lengthMenu: [4, 10, 25, 50],
        lengthChange: false,
        ordering: false,
        info: true,
        responsive: true,
        language: {
            decimal: "",
            emptyTable: "No hay datos disponibles en la tabla",
            info: "Mostrando _START_ a _END_ de _TOTAL_ registros",
            infoEmpty: "Mostrando 0 a 0 de 0 registros",
            infoFiltered: "(filtrado de _MAX_ registros totales)",
            lengthMenu: "Mostrar _MENU_ registros",
            loadingRecords: "Cargando...",
            processing: "Procesando...",
            search: "Buscar:",
            zeroRecords: "No se encontraron resultados",
            paginate: {
            first: "Primero",
            last: "Último",
            next: "Siguiente",
            previous: "Anterior"
            },
            aria: {
            sortAscending: ": activar para ordenar ascendente",
            sortDescending: ": activar para ordenar descendente"
            }
        },
    });
});


document.addEventListener("DOMContentLoaded", function () {
    const modalRegistrar = document.getElementById("modalRegistrar");

    modalRegistrar.addEventListener("show.bs.modal", function (event) {
        const button = event.relatedTarget; // Botón que abre el modal
        const id = button.getAttribute("data-id");

        // Cambiar título y botón según si es nuevo o edición
        const modalTitulo = modalRegistrar.querySelector("#modalTitulo");
        const botonGuardar = modalRegistrar.querySelector(".modal-footer button[type='submit']");

        if (id) {
            modalTitulo.innerHTML = `<i class="fa-solid fa-pen-to-square me-2"></i> Actualizar Resolución`;
            botonGuardar.innerHTML = `<i class="fa-solid fa-save me-1"></i> Actualizar`;
        } else {
            modalTitulo.innerHTML = `<i class="fa-solid fa-plus me-2"></i> Registro Resolución`;
            botonGuardar.innerHTML = `<i class="fa-solid fa-floppy-disk me-1"></i> Guardar`;
        }

        // Llenar campos
        modalRegistrar.querySelector("#expediente_id").value = id || "";
        modalRegistrar.querySelector("#director").value = button.getAttribute("data-director") || "";
        modalRegistrar.querySelector("#genero").value = button.getAttribute("data-genero") || "";
        modalRegistrar.querySelector("#num_expediente").value = button.getAttribute("data-expediente") || "";
        modalRegistrar.querySelector("#tipo_atencion").value = button.getAttribute("data-tipo") || "";
        modalRegistrar.querySelector("#anio_inicio").value = button.getAttribute("data-anio_inicio") || "";
        modalRegistrar.querySelector("#estado").value = button.getAttribute("data-estado") || "";
        modalRegistrar.querySelector("#resolucion").value = button.getAttribute("data-resolucion") || "";
        modalRegistrar.querySelector("#fecha_emision").value = button.getAttribute("data-fecha") || "";
        modalRegistrar.querySelector("#correo").value = button.getAttribute("data-correo") || "";
        modalRegistrar.querySelector("#oficio").value = button.getAttribute("data-oficio") || "";
        modalRegistrar.querySelector("#detalle").value = button.getAttribute("data-detalle") || "";
        const codigo_local = button.getAttribute("data-codigo_local");
        const modalidad = button.getAttribute("data-modalidad");
        const archivo = button.getAttribute("data-archivo");
        const archivoActual = modalRegistrar.querySelector("#archivo_actual");
        archivoActual.innerHTML = archivo
            ? `Archivo actual: <a href="/static/conei_pdf/${modalidad}_${codigo_local}/${archivo}" target="_blank">Ver PDF</a>`
            : "";
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const anioSelect = document.getElementById("anioSelect");

    let estadoChart, historicoChart;

    // Función para cargar los datos del reporte
    function cargarDatos(anio) {
        fetch(`/reportes/api/reporte/${anio}`)  // 🔹 URL corregida
            .then(res => res.json())
            .then(data => {

                // Construir select de años dinámicamente
                anioSelect.innerHTML = "";
                for (let y = 2018; y <= data.anio_actual; y++) {
                    const opt = document.createElement("option");
                    opt.value = y;
                    opt.textContent = y;
                    if (y === data.anio) opt.selected = true;
                    anioSelect.appendChild(opt);
                }

                // Actualizar enlace de descarga
                document.getElementById("btnDescargar").href = `/reportes/reporte/exportar/${data.anio}`; // 🔹 URL corregida

                // Totales
                document.getElementById("totalIE").textContent = data.modalidad_estado.total || 0;

                let validados = data.validados_observados.find(e => e.estado === "Validado")?.total || 0;
                let observados = data.validados_observados.find(e => e.estado === "Observado")?.total || 0;
                let omisos = data.validados_observados.find(e => e.estado === "Omiso")?.total || 0;

                document.getElementById("validados").textContent = validados;
                document.getElementById("observados").textContent = observados;
                document.getElementById("omisos").textContent = omisos;

                // Actualizar título histórico
                document.getElementById("titulo-historico").innerText = `Histórico 2018 – ${data.anio_actual}`;

                // Gráfico de Estados (Doughnut)
                if (estadoChart) estadoChart.destroy();
                estadoChart = new Chart(document.getElementById("estadoChart"), {
                    type: "doughnut",
                    data: {
                        labels: ["Validados", "Observados", "Omisos"],
                        datasets: [{
                            data: [validados, observados, omisos],
                            backgroundColor: ["#198754", "#ffc107", "#dc3545"]
                        }]
                    }
                });

                // Gráfico Histórico (Line)
                if (historicoChart) historicoChart.destroy();
                historicoChart = new Chart(document.getElementById("historicoChart"), {
                    type: "line",
                    data: {
                        labels: data.historico.map(h => h.anio),
                        datasets: [{
                            label: "IIEE con CONEI registrados",
                            data: data.historico.map(h => h.total),
                            borderColor: "#007bff",
                            fill: false,
                            tension: 0.2
                        }]
                    }
                });
            })
            .catch(err => console.error("Error cargando datos:", err));
    }

    // Cargar al iniciar con el año actual
    cargarDatos(0); // 🔹 Backend interpreta 0 como año actual

    // Evento al cambiar año en el select
    anioSelect.addEventListener("change", () => {
        cargarDatos(parseInt(anioSelect.value));
    });
});
