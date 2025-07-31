// Excel Upload Interface JavaScript

// ============================================================================
// Variables Globales
// ============================================================================

// Archivo actualmente seleccionado por el usuario
let currentFile = null;

// Datos previsualizados del archivo Excel/CSV (columnas y primeras filas)
let previewData = null;

// Tablas disponibles obtenidas desde la API
// Se carga al iniciar la página y se actualiza cuando se crean nuevas tablas
let availableTables = {};

// Definición de columnas para tablas existentes
let tableColumns = {
    'feriados': ['pais', 'feriado', 'fecha'],
    'diccionario_catalogo_empresa': ['empresa', 'valor']
};

// ============================================================================
// Inicialización de la Página
// ============================================================================

// Función que se ejecuta cuando la página se carga completamente
// Configura todos los event listeners y carga datos iniciales
document.addEventListener('DOMContentLoaded', function() {
    // Configurar la zona de drag & drop para archivos
    initializeDropZone();
    
    // Configurar el input de archivo oculto
    initializeFileInput();
    
    // Configurar el selector de tablas
    initializeTableSelect();
    
    // Cargar las tablas disponibles desde la API
    loadAvailableTables();
});

// ============================================================================
// Inicialización de la zona de arrastrar y soltar archivos
// ============================================================================
/**
 * Inicializa la zona de arrastrar y soltar (drag & drop) para subir archivos.
 */
function initializeDropZone() {
    const dropZone = document.getElementById('dropZone'); // Zona de drop
    const fileInput = document.getElementById('fileInput'); // Input oculto de archivos

    // Cuando se arrastra un archivo sobre la zona, resalta visualmente
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault(); // Previene comportamiento por defecto
        dropZone.classList.add('dragover'); // Añade clase de resaltado
    });

    // Cuando el archivo sale de la zona, quita el resaltado
    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    });

    // Cuando se suelta un archivo, lo procesa y quita el resaltado
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files; // Archivos soltados
        if (files.length > 0) {
            handleFile(files[0]); // Procesa el primer archivo
        }
    });

    // Si el usuario hace click en la zona, abre el selector de archivos
    dropZone.addEventListener('click', function() {
        fileInput.click();
    });
}

// ============================================================================
// Inicialización del input de archivo
// ============================================================================
/**
 * Inicializa el input de archivo oculto para seleccionar archivos manualmente.
 */
function initializeFileInput() {
    const fileInput = document.getElementById('fileInput');
    
    // Cuando el usuario selecciona un archivo desde el explorador
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
}

// ============================================================================
// Inicialización del selector de tablas
// ============================================================================
/**
 * Inicializa el selector de tablas y gestiona los cambios de selección.
 */
function initializeTableSelect() {
    const tableSelect = document.getElementById('tableSelect');
    
    // Cuando el usuario selecciona una tabla
    tableSelect.addEventListener('change', function() {
        const selectedTable = this.value;
        if (selectedTable === 'create_new') {
            showCreateTableForm(); // Mostrar formulario para crear nueva tabla
        } else if (selectedTable && previewData) {
            showColumnMapping(selectedTable); // Mostrar mapeo de columnas
            document.getElementById('uploadBtn').classList.remove('d-none');
        } else {
            // Ocultar interfaces si no hay selección válida
            document.getElementById('columnMapping').classList.add('d-none');
            document.getElementById('createTableForm').classList.add('d-none');
            document.getElementById('uploadBtn').classList.add('d-none');
        }
    });
}

// ============================================================================
// Manejo de Archivos
// ============================================================================

/**
 * Función que se ejecuta cuando el usuario selecciona un archivo.
 * Valida el archivo y lo procesa para mostrar una previsualización.
 */
function handleFile(file) {
    // Lista de tipos MIME permitidos para archivos Excel y CSV
    const allowedTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx (Excel 2007+)
        'application/vnd.ms-excel', // .xls (Excel 97-2003)
        'text/csv' // .csv (archivos de texto separados por comas)
    ];
    
    // Validar el tipo de archivo (MIME o extensión)
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls|csv)$/i)) {
        showToast('error', 'Tipo de archivo no válido', 'Por favor selecciona un archivo Excel (.xlsx, .xls) o CSV (.csv)');
        return;
    }

    // Validar el tamaño del archivo (máximo 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showToast('error', 'Archivo demasiado grande', 'El archivo no puede ser mayor a 10MB');
        return;
    }

    // Guardar el archivo en la variable global para uso posterior
    currentFile = file;
    
    // Mostrar información del archivo en la interfaz
    showFileInfo(file);
    
    // Subir el archivo al servidor para obtener una previsualización
    uploadFileForPreview(file);
}

/**
 * Muestra la información del archivo seleccionado en la interfaz.
 */
function showFileInfo(file) {
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');

    fileName.textContent = file.name; // Nombre del archivo
    fileSize.textContent = formatFileSize(file.size); // Tamaño formateado
    fileInfo.classList.remove('d-none'); // Mostrar sección
}

/**
 * Carga las tablas disponibles desde la API y actualiza el selector.
 */
async function loadAvailableTables() {
    try {
        const response = await fetch('/api/v1/upload/tables'); // Llama a la API
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                availableTables = result.tables; // Actualiza variable global
                updateTableSelect(); // Refresca el selector de tablas
            }
        }
    } catch (error) {
        console.error('Error loading tables:', error);
    }
}

/**
 * Actualiza el selector de tablas con las opciones disponibles.
 */
function updateTableSelect() {
    const tableSelect = document.getElementById('tableSelect');
    const currentValue = tableSelect.value;
    
    // Limpiar opciones existentes
    tableSelect.innerHTML = '<option value="">Selecciona una tabla...</option>';
    
    // Agregar tablas disponibles
    Object.keys(availableTables).forEach(tableName => {
        const table = availableTables[tableName];
        const option = document.createElement('option');
        option.value = tableName;
        option.textContent = table.name;
        tableSelect.appendChild(option);
    });
    
    // Agregar opción para crear nueva tabla
    const createOption = document.createElement('option');
    createOption.value = 'create_new';
    createOption.textContent = '➕ Crear Nueva Tabla';
    tableSelect.appendChild(createOption);
    
    // Restaurar selección previa si existe
    if (currentValue && tableSelect.querySelector(`option[value="${currentValue}"]`)) {
        tableSelect.value = currentValue;
    }
}

/**
 * Formatea el tamaño de archivo en una cadena legible.
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Limpia la selección de archivo y resetea la interfaz.
 */
function clearFile() {
    currentFile = null;
    previewData = null;
    
    document.getElementById('fileInfo').classList.add('d-none');
    document.getElementById('previewSection').classList.add('d-none');
    document.getElementById('columnMapping').classList.add('d-none');
    document.getElementById('uploadBtn').classList.add('d-none');
    document.getElementById('progressCard').classList.add('d-none');
    document.getElementById('resultsCard').classList.add('d-none');
    
    document.getElementById('fileInput').value = '';
    document.getElementById('tableSelect').value = '';
}

/**
 * Sube el archivo al servidor para obtener una previsualización.
 */
// Esta función se encarga de subir un archivo al servidor para obtener una previsualización de su contenido.
// Es asincrónica porque utiliza 'fetch' para hacer una petición HTTP al backend.

async function uploadFileForPreview(file) {
    // Creamos un objeto FormData y le agregamos el archivo seleccionado.
    const formData = new FormData();
    formData.append('file', file);

    try {
        // Mostramos un mensaje al usuario indicando que el archivo está siendo procesado.
        showToast('info', 'Procesando archivo...', 'Analizando contenido del archivo');
        
        // Hacemos una petición POST al endpoint '/api/v1/upload/preview' enviando el archivo.
        const response = await fetch('/api/v1/upload/preview', {
            method: 'POST',
            body: formData
        });

        // Si la respuesta no es exitosa (código diferente de 2xx), lanzamos un error.
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Convertimos la respuesta a JSON.
        const result = await response.json();
        
        // Si el backend indica éxito, guardamos los datos de previsualización y los mostramos en la interfaz.
        if (result.success) {
            previewData = result.data; // Guardar datos de previsualización
            showPreview(previewData); // Mostrar preview en la interfaz
            showToast('success', 'Archivo procesado', 'Datos cargados correctamente');
        } else {
            // Si el backend indica error, lanzamos un error con el mensaje recibido.
            throw new Error(result.message || 'Error al procesar el archivo');
        }
    } catch (error) {
        // Si ocurre cualquier error, lo mostramos en consola, notificamos al usuario y limpiamos la interfaz.
        console.error('Error uploading file:', error);
        showToast('error', 'Error al procesar archivo', error.message);
        clearFile();
    }
}

/**
 * Muestra la previsualización de los datos del archivo en una tabla.
 */
function showPreview(data) {
    const previewSection = document.getElementById('previewSection');
    const tableHead = document.getElementById('previewTableHead');
    const tableBody = document.getElementById('previewTableBody');

    // Crear encabezado de la tabla
    tableHead.innerHTML = '';
    const headerRow = document.createElement('tr');
    data.columns.forEach(column => {
        const th = document.createElement('th');
        th.textContent = column;
        th.className = 'text-center';
        headerRow.appendChild(th);
    });
    tableHead.appendChild(headerRow);

    // Crear cuerpo de la tabla (primeras 10 filas)
    tableBody.innerHTML = '';
    const rowsToShow = Math.min(10, data.rows.length);
    
    for (let i = 0; i < rowsToShow; i++) {
        const row = document.createElement('tr');
        data.columns.forEach(column => {
            const td = document.createElement('td');
            td.textContent = data.rows[i][column] || '';
            td.className = 'text-center';
            row.appendChild(td);
        });
        tableBody.appendChild(row);
    }

    // Mostrar mensaje si hay más filas
    if (data.rows.length > 10) {
        const infoRow = document.createElement('tr');
        const infoCell = document.createElement('td');
        infoCell.colSpan = data.columns.length;
        infoCell.textContent = `... y ${data.rows.length - 10} filas más`;
        infoCell.className = 'text-center text-muted small';
        infoRow.appendChild(infoCell);
        tableBody.appendChild(infoRow);
    }

    previewSection.classList.remove('d-none');
}

/**
 * Muestra la interfaz de mapeo de columnas para la tabla seleccionada.
 */
function showColumnMapping(selectedTable) {
    const mappingContainer = document.getElementById('mappingContainer');
    const columnMapping = document.getElementById('columnMapping');
    
    mappingContainer.innerHTML = '';
    
    // Obtener columnas de la tabla seleccionada
    let targetColumns = tableColumns[selectedTable] || [];
    
    // Crear filas de mapeo para cada columna destino
    targetColumns.forEach(targetCol => {
        const mappingRow = document.createElement('div');
        mappingRow.className = 'mapping-row';
        
        mappingRow.innerHTML = `
            <div class="row align-items-center">
                <div class="col-5">
                    <label class="form-label small mb-1">${targetCol.toUpperCase()}</label>
                    <select class="form-select form-select-sm" data-target="${targetCol}">
                        <option value="">-- Seleccionar columna --</option>
                        ${previewData.columns.map(col => 
                            `<option value="${col}">${col}</option>`
                        ).join('')}
                    </select>
                </div>
                <div class="col-2 text-center">
                    <i class="bi bi-arrow-right text-muted"></i>
                </div>
                <div class="col-5">
                    <label class="form-label small mb-1">Columna Destino</label>
                    <input type="text" class="form-control form-control-sm" value="${targetCol}" readonly>
                </div>
            </div>
        `;
        
        mappingContainer.appendChild(mappingRow);
    });
    
    columnMapping.classList.remove('d-none');
}

/**
 * Muestra el formulario para crear una nueva tabla SQL real
 */
function showCreateTableForm() {
    const createTableForm = document.getElementById('createTableForm');
    const columnMapping = document.getElementById('columnMapping');
    
    // Ocultar mapeo de columnas
    columnMapping.classList.add('d-none');
    
    // Mostrar formulario de creación
    createTableForm.classList.remove('d-none');
    
    // Generar campos de columnas basados en el preview
    const columnsContainer = document.getElementById('newTableColumns');
    columnsContainer.innerHTML = '';
    
    previewData.columns.forEach((col, index) => {
        const columnRow = document.createElement('div');
        columnRow.className = 'mapping-row';
        columnRow.innerHTML = `
            <div class="row align-items-center">
                <div class="col-4">
                    <label class="form-label small mb-1">Nombre de Columna</label>
                    <input type="text" class="form-control form-control-sm" value="${col}" readonly>
                </div>
                <div class="col-3">
                    <label class="form-label small mb-1">Tipo de Dato</label>
                    <select class="form-select form-select-sm" data-column="${col}">
                        <option value="TEXT">Texto</option>
                        <option value="INTEGER">Número Entero</option>
                        <option value="REAL">Número Decimal</option>
                        <option value="DATE">Fecha</option>
                        <option value="BOOLEAN">Booleano</option>
                    </select>
                </div>
                <div class="col-3">
                    <label class="form-label small mb-1">Requerido</label>
                    <select class="form-select form-select-sm" data-required="${col}">
                        <option value="true">Sí</option>
                        <option value="false">No</option>
                    </select>
                </div>
                <div class="col-2">
                    <label class="form-label small mb-1">Acción</label>
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeColumn(this)">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        `;
        columnsContainer.appendChild(columnRow);
    });
    
    document.getElementById('uploadBtn').classList.remove('d-none');
}

/**
 * Sube los datos a la base de datos, ya sea en una tabla existente o creando una nueva.
 */
async function uploadToDatabase() {
    const selectedTable = document.getElementById('tableSelect').value;
    
    // Mostrar barra de progreso
    document.getElementById('progressCard').classList.remove('d-none');
    document.getElementById('uploadBtn').disabled = true;
    
    try {
        let uploadData = {
            table_name: selectedTable,
            column_mapping: {},
            data: previewData.rows,
            create_new_table: false,
            new_table_info: null
        };

        if (selectedTable === 'create_new') {
            // Crear nueva tabla SQL real
            const tableName = document.getElementById('newTableName').value;
            const tableDisplayName = document.getElementById('newTableDisplayName').value;
            const tableDescription = document.getElementById('newTableDescription').value;
            
            if (!tableName || !tableDisplayName) {
                throw new Error('Por favor completa el nombre de la tabla y nombre para mostrar');
            }
            
            // Obtener información de columnas
            const columns = [];
            const columnRows = document.querySelectorAll('#newTableColumns .mapping-row');
            columnRows.forEach(row => {
                const columnName = row.querySelector('input[readonly]').value;
                const dataType = row.querySelector('select[data-column]').value;
                const required = row.querySelector('select[data-required]').value === 'true';
                
                columns.push({
                    name: columnName,
                    display_name: columnName,
                    data_type: dataType,
                    required: required
                });
            });
            
            uploadData.create_new_table = true;
            uploadData.new_table_info = {
                table_name: tableName,
                display_name: tableDisplayName,
                description: tableDescription,
                columns: columns
            };
            
                         // Crear mapping automático (columna origen = columna destino)
             columns.forEach(col => {
                 uploadData.column_mapping[col.name] = col.name;
             });
            
        } else {
            // Tabla existente: obtener mapeo de columnas
            const mappingSelects = document.querySelectorAll('#mappingContainer select');
            
            // Validar que todas las columnas estén mapeadas
            let isValid = true;
             
            mappingSelects.forEach(select => {
                const targetCol = select.dataset.target;
                const sourceCol = select.value;
                
                if (!sourceCol) {
                    isValid = false;
                    select.classList.add('is-invalid');
                                 } else {
                     select.classList.remove('is-invalid');
                     uploadData.column_mapping[targetCol] = sourceCol;
                 }
            });
            
            if (!isValid) {
                throw new Error('Por favor mapea todas las columnas requeridas');
            }
        }

        // Enviar datos al backend para insertar en la base de datos
        const response = await fetch('/api/v1/upload/insert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(uploadData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.success) {
            showResults(result); // Mostrar resultados en la interfaz
            let message = `Se insertaron ${result.inserted_count} registros correctamente`;
            if (result.table_created) {
                message += ` y se creó la tabla "${result.new_table_name}"`;
            }
            showToast('success', 'Operación exitosa', message);
        } else {
            throw new Error(result.message || 'Error al insertar datos');
        }
    } catch (error) {
        console.error('Error uploading data:', error);
        showToast('error', 'Error al insertar datos', error.message);
    } finally {
        document.getElementById('progressCard').classList.add('d-none');
        document.getElementById('uploadBtn').disabled = false;
    }
}

/**
 * Muestra los resultados de la carga de datos en la interfaz.
 */
function showResults(result) {
    const resultsCard = document.getElementById('resultsCard');
    const resultsContent = document.getElementById('resultsContent');
    
    resultsContent.innerHTML = `
        <div class="text-center">
            <i class="bi bi-check-circle text-success display-4"></i>
            <h5 class="mt-3 text-success">¡Datos insertados exitosamente!</h5>
            <p class="text-muted">Se procesaron ${result.total_count} registros</p>
            <div class="row text-center">
                <div class="col-6">
                    <div class="bg-success bg-opacity-10 rounded p-2">
                        <strong class="text-success">${result.inserted_count}</strong>
                        <br><small>Insertados</small>
                    </div>
                </div>
                <div class="col-6">
                    <div class="bg-warning bg-opacity-10 rounded p-2">
                        <strong class="text-warning">${result.skipped_count}</strong>
                        <br><small>Omitidos</small>
                    </div>
                </div>
            </div>
            ${result.errors && result.errors.length > 0 ? `
                <div class="mt-3">
                    <h6 class="text-danger">Errores encontrados:</h6>
                    <div class="small text-muted">
                        ${result.errors.slice(0, 3).join('<br>')}
                        ${result.errors.length > 3 ? `<br>... y ${result.errors.length - 3} errores más` : ''}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
    
    resultsCard.classList.remove('d-none');
}

/**
 * Muestra una notificación tipo toast en la interfaz.
 */
function showToast(type, title, message) {
    const toast = document.getElementById('toast');
    const toastIcon = document.getElementById('toastIcon');
    const toastTitle = document.getElementById('toastTitle');
    const toastBody = document.getElementById('toastBody');
    
    // Definir iconos y colores según el tipo de mensaje
    const icons = {
        'success': 'bi-check-circle text-success',
        'error': 'bi-x-circle text-danger',
        'warning': 'bi-exclamation-triangle text-warning',
        'info': 'bi-info-circle text-info'
    };
    
    toastIcon.className = `bi ${icons[type] || icons.info}`;
    toastTitle.textContent = title;
    toastBody.textContent = message;
    
    // Mostrar el toast usando Bootstrap
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

/**
 * Actualiza la barra de progreso de la interfaz.
 */
function updateProgress(percent, text) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    
    progressBar.style.width = `${percent}%`;
    progressBar.setAttribute('aria-valuenow', percent);
    progressText.textContent = text;
}

/**
 * Elimina una columna del formulario de creación de tabla
 */
function removeColumn(button) {
    const row = button.closest('.mapping-row');
    row.remove();
}

/**
 * Función de debug para verificar el estado
 */
function showDebugInfo() {
    const debugInfo = {
        currentFile: currentFile ? currentFile.name : 'No file',
        previewData: previewData ? `Columns: ${previewData.columns.length}, Rows: ${previewData.rows.length}` : 'No preview',
        selectedTable: document.getElementById('tableSelect').value,
        uploadBtnVisible: !document.getElementById('uploadBtn').classList.contains('d-none'),
        createTableFormVisible: !document.getElementById('createTableForm').classList.contains('d-none'),
        columnMappingVisible: !document.getElementById('columnMapping').classList.contains('d-none')
    };
    
    console.log('Debug Info:', debugInfo);
    alert(`Debug Info:\n${JSON.stringify(debugInfo, null, 2)}`);
} 