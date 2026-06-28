document.addEventListener('DOMContentLoaded', () => {
    const pdfSelect = document.getElementById('pdfSelect');
    const profileSelect = document.getElementById('profileSelect');
    const noPdfMessage = document.getElementById('noPdfMessage');
    const pdfForm = document.getElementById('pdfForm');
    const dynamicFieldsContainer = document.getElementById('dynamicFieldsContainer');
    const actionButtons = document.getElementById('actionButtons');
    const hiddenPdfName = document.getElementById('hiddenPdfName');
    const hiddenFieldData = document.getElementById('hiddenFieldData');
    
    const saveModal = new bootstrap.Modal(document.getElementById('saveProfileModal'));
    let currentFields = {};

    // 1. PDF-Auswahl ändert sich
    pdfSelect.addEventListener('change', async (e) => {
        const filename = e.target.value;
        if (!filename) return;

        // Reset UI
        dynamicFieldsContainer.innerHTML = '<div class="text-center w-100"><div class="spinner-border text-primary" role="status"></div><p>Lese PDF-Struktur...</p></div>';
        noPdfMessage.style.display = 'none';
        pdfForm.style.display = 'block';
        hiddenPdfName.value = filename;

        try {
            const response = await fetch(`/parse-pdf/${filename}`);
            const data = await response.json();
            currentFields = data.fields;
            
            renderFields(data.fields);
            profileSelect.disabled = false;
            actionButtons.style.display = 'block';
        } catch (error) {
            console.error('Error parsing PDF:', error);
            dynamicFieldsContainer.innerHTML = '<div class="alert alert-danger">Fehler beim Einlesen der PDF-Struktur.</div>';
        }
    });

    // Dynamische Inputs rendern
    function renderFields(fields) {
        dynamicFieldsContainer.innerHTML = '';
        if (Object.keys(fields).length === 0) {
            dynamicFieldsContainer.innerHTML = '<div class="alert alert-warning w-100">Keine interaktiven Formularfelder in dieser PDF gefunden.</div>';
            return;
        }

        for (const [fieldName, fieldInfo] of Object.entries(fields)) {
            const col = document.createElement('div');
            col.className = 'col-md-6 mb-3';
            
            // Bereinigung für HTML IDs/Names
            const cleanName = fieldName.replace(/[^a-zA-Z0-9-_]/g, '_');

            // Unterscheidung Checkbox vs Textfeld anhand des Typs
            if (fieldInfo.type === '/Btn') {
                col.innerHTML = `
                    <div class="form-check mt-4">
                        <input class="form-check-input pdf-input" type="checkbox" id="${cleanName}" data-fieldname="${fieldName}">
                        <label class="form-check-label text-truncate d-block" for="${cleanName}" title="${fieldName}">
                            ${fieldName}
                        </label>
                    </div>
                `;
            } else {
                col.innerHTML = `
                    <label class="form-label text-truncate d-block" for="${cleanName}" title="${fieldName}">${fieldName}</label>
                    <input type="text" class="form-control pdf-input" id="${cleanName}" data-fieldname="${fieldName}" value="${fieldInfo.value || ''}">
                `;
            }
            dynamicFieldsContainer.appendChild(col);
        }
    }

    // 2. Profil laden
    profileSelect.addEventListener('change', async (e) => {
        const profileName = e.target.value;
        if (!profileName) return;

        try {
            const response = await fetch(`/load-profile/${profileName}`);
            const profileData = await response.json();

            // Werte in die GUI-Felder mappen
            document.querySelectorAll('.pdf-input').forEach(input => {
                const fName = input.getAttribute('data-fieldname');
                if (profileData[fName] !== undefined) {
                    if (input.type === 'checkbox') {
                        input.checked = profileData[fName] === 'Yes' || profileData[fName] === true;
                    } else {
                        input.value = profileData[fName];
                    }
                }
            });
        } catch (error) {
            console.error('Error loading profile:', error);
        }
    });

    // 3. Profil Speichern Trigger
    document.getElementById('btnSaveProfile').addEventListener('click', () => {
        saveModal.show();
    });

    document.getElementById('btnConfirmSaveProfile').addEventListener('click', async () => {
        const profileName = document.getElementById('profileNameInput').value.trim();
        if (!profileName) return;

        const payload = {
            profile_name: profileName,
            fields: serializeFormFields()
        };

        try {
            const response = await fetch('/save-profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const resData = await response.json();
            if (resData.status === 'success') {
                saveModal.hide();
                location.reload(); // Aktualisiert die Profilliste im Dropdown
            }
        } catch (error) {
            console.error('Error saving profile:', error);
        }
    });

    // Hilfsfunktion zur Aggregation der Werte
    function serializeFormFields() {
        const data = {};
        document.querySelectorAll('.pdf-input').forEach(input => {
            const fName = input.getAttribute('data-fieldname');
            if (input.type === 'checkbox') {
                data[fName] = input.checked ? '/Yes' : '/Off'; // PDF-Standardwerte für Checkboxen
            } else {
                data[fName] = input.value;
            }
        });
        return data;
    }

    // Interzepiert den Submit, um JSON-Formulardaten ins Hidden Field zu packen
    pdfForm.addEventListener('submit', (e) => {
        hiddenFieldData.value = JSON.stringify(serializeFormFields());
    });
});
