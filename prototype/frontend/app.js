"use strict";

/*
 * Siyana AI Phase 4C.2 frontend.
 *
 * Provides:
 * - Model health monitoring
 * - English, French and Arabic interface localization
 * - Local PDF and TXT import
 * - Imported-document listing and deletion
 * - Grounded chat using local SQLite FTS5 retrieval
 * - Local source and citation display
 */

const translations = {
    en: {
        documentTitle: "Siyana AI",
        brandSubtitle: "Offline industrial-maintenance support",
        statusChecking: "Checking local model...",
        statusReady: "Local model ready",
        statusUnavailable: "Local model unavailable",

        heroTitle:
            "Safer preliminary maintenance guidance, completely offline.",
        heroDescription:
            "Describe an industrial-machine symptom. Siyana AI uses the local Qwen3-4B model and optional local machine manuals to generate structured guidance.",

        privacyTitle: "Local processing",
        privacyText:
            "Questions, manuals, searches and answers remain on this computer.",

        manualHeading: "Machine manuals",
        manualDescription:
            "Import a text-based PDF or TXT manual. The document is processed and searched locally on this computer.",
        selectManualText: "Select local manual",
        manualTypesText: "PDF or TXT, maximum 25 MB",
        noFileSelected: "No file selected",
        importManual: "Import manual",
        importingManual: "Importing locally...",
        documentSingle: "document",
        documentPlural: "documents",
        chunkSingle: "searchable section",
        chunkPlural: "searchable sections",
        documentsEmptyTitle: "No local manuals imported",
        documentsEmptyText:
            "Siyana AI can still provide general preliminary guidance without a manual.",
        importedSuccessfully: "Document imported locally.",
        deleteDocument: "Delete",
        deleteConfirmation:
            "Delete this local manual and all its indexed sections?",
        documentDeleted: "Document deleted locally.",
        pages: "pages",
        sections: "sections",
        fileSize: "File size",
        importDate: "Imported",

        questionHeading: "Describe the situation",
        questionHelp:
            "Add the available machine information. Do not enter secrets or personal data.",
        languageLabel: "Language",
        machineNameLabel: "Machine or equipment",
        machineNamePlaceholder: "Example: Pneumatic press",
        machineModelLabel: "Model, if known",
        machineModelPlaceholder: "Example: PX-200",
        questionLabel: "Symptom or question",
        questionPlaceholder:
            "Example: The pneumatic cylinder has become slow in both directions.",
        contextLabel: "Additional context, if available",
        contextPlaceholder:
            "Operating load, alarm text, recent changes, observations...",

        useDocumentsTitle: "Search local manuals",
        useDocumentsText:
            "Include relevant local excerpts and citations when available.",
        maximumSourcesLabel: "Maximum sources",

        safetyReminderTitle: "Safety reminder",
        safetyReminderText:
            "Stop and isolate hazardous energy before inspection or maintenance.",

        submitButton: "Ask Siyana AI",
        submitting: "Generating locally...",

        emptyTitle: "The local assistant is ready",
        emptyText:
            "Submit an industrial-maintenance question to view a structured response.",

        answerTitle: "Preliminary guidance",
        copy: "Copy",
        copied: "Copied",
        important: "Important",
        errorTitle: "Unable to generate a response",
        genericError:
            "The local application could not complete this action. Check the backend terminal and try again.",

        modelLabel: "Model",
        durationLabel: "Duration",
        offlineLabel: "Offline inference",
        retrievalUsed: "Local manuals used",
        retrievalNotUsed: "No relevant manual source",

        citationsTitle: "Retrieved manual excerpts",
        sourceSingle: "source",
        sourcePlural: "sources",
        page: "Page",

        limitationsTitle: "Current prototype capabilities",
        capabilityOneTitle: "Local multilingual AI",
        capabilityOneText:
            "English, French and Arabic guidance from Qwen3-4B.",
        capabilityTwoTitle: "Local document grounding",
        capabilityTwoText:
            "PDF and TXT manuals are searched through SQLite FTS5.",
        capabilityThreeTitle: "Safety focused",
        capabilityThreeText:
            "Refuses guard bypasses and unsafe maintenance procedures."
    },

    fr: {
        documentTitle: "Siyana AI",
        brandSubtitle: "Assistance locale à la maintenance industrielle",
        statusChecking: "Vérification du modèle local...",
        statusReady: "Modèle local prêt",
        statusUnavailable: "Modèle local indisponible",

        heroTitle:
            "Des conseils préliminaires de maintenance plus sûrs, entièrement hors ligne.",
        heroDescription:
            "Décrivez le symptôme d'une machine industrielle. Siyana AI utilise le modèle local Qwen3-4B et les manuels locaux disponibles.",

        privacyTitle: "Traitement local",
        privacyText:
            "Les questions, les manuels, les recherches et les réponses restent sur cet ordinateur.",

        manualHeading: "Manuels des machines",
        manualDescription:
            "Importez un manuel PDF textuel ou TXT. Le document est traité et recherché localement.",
        selectManualText: "Sélectionner un manuel local",
        manualTypesText: "PDF ou TXT, maximum 25 Mo",
        noFileSelected: "Aucun fichier sélectionné",
        importManual: "Importer le manuel",
        importingManual: "Importation locale...",
        documentSingle: "document",
        documentPlural: "documents",
        chunkSingle: "section indexée",
        chunkPlural: "sections indexées",
        documentsEmptyTitle: "Aucun manuel local importé",
        documentsEmptyText:
            "Siyana AI peut fournir des conseils généraux sans manuel.",
        importedSuccessfully: "Document importé localement.",
        deleteDocument: "Supprimer",
        deleteConfirmation:
            "Supprimer ce manuel local et toutes ses sections indexées ?",
        documentDeleted: "Document supprimé localement.",
        pages: "pages",
        sections: "sections",
        fileSize: "Taille",
        importDate: "Importé",

        questionHeading: "Décrivez la situation",
        questionHelp:
            "Ajoutez les informations disponibles sur la machine. Ne saisissez pas de données personnelles ou confidentielles.",
        languageLabel: "Langue",
        machineNameLabel: "Machine ou équipement",
        machineNamePlaceholder: "Exemple : Presse pneumatique",
        machineModelLabel: "Modèle, si connu",
        machineModelPlaceholder: "Exemple : PX-200",
        questionLabel: "Symptôme ou question",
        questionPlaceholder:
            "Exemple : Le vérin pneumatique est devenu lent dans les deux sens.",
        contextLabel: "Contexte supplémentaire, si disponible",
        contextPlaceholder:
            "Charge, texte de l'alarme, changements récents, observations...",

        useDocumentsTitle: "Rechercher dans les manuels locaux",
        useDocumentsText:
            "Inclure des extraits locaux pertinents et leurs références.",
        maximumSourcesLabel: "Nombre maximal de sources",

        safetyReminderTitle: "Rappel de sécurité",
        safetyReminderText:
            "Arrêtez la machine et isolez les énergies dangereuses avant toute intervention.",

        submitButton: "Interroger Siyana AI",
        submitting: "Génération locale...",

        emptyTitle: "L'assistant local est prêt",
        emptyText:
            "Envoyez une question de maintenance pour afficher une réponse structurée.",

        answerTitle: "Conseils préliminaires",
        copy: "Copier",
        copied: "Copié",
        important: "Important",
        errorTitle: "Impossible d'effectuer l'action",
        genericError:
            "L'application locale n'a pas pu effectuer cette action. Vérifiez le terminal du backend.",

        modelLabel: "Modèle",
        durationLabel: "Durée",
        offlineLabel: "Inférence hors ligne",
        retrievalUsed: "Manuels locaux utilisés",
        retrievalNotUsed: "Aucune source locale pertinente",

        citationsTitle: "Extraits des manuels consultés",
        sourceSingle: "source",
        sourcePlural: "sources",
        page: "Page",

        limitationsTitle: "Fonctions du prototype actuel",
        capabilityOneTitle: "IA multilingue locale",
        capabilityOneText:
            "Conseils en anglais, français et arabe avec Qwen3-4B.",
        capabilityTwoTitle: "Appui sur les documents locaux",
        capabilityTwoText:
            "Les manuels PDF et TXT sont recherchés avec SQLite FTS5.",
        capabilityThreeTitle: "Axé sur la sécurité",
        capabilityThreeText:
            "Refuse les contournements et les interventions dangereuses."
    },

    ar: {
        documentTitle: "صيانة AI",
        brandSubtitle: "دعم محلي للصيانة الصناعية",
        statusChecking: "جارٍ التحقق من النموذج المحلي...",
        statusReady: "النموذج المحلي جاهز",
        statusUnavailable: "النموذج المحلي غير متاح",

        heroTitle:
            "إرشادات أولية أكثر أماناً للصيانة، تعمل بالكامل دون إنترنت.",
        heroDescription:
            "صف عَرَضاً متعلقاً بآلة صناعية. يستخدم Siyana AI النموذج المحلي وأدلة الآلات المحلية المتوفرة.",

        privacyTitle: "معالجة محلية",
        privacyText:
            "تبقى الأسئلة والأدلة وعمليات البحث والإجابات على هذا الحاسوب.",

        manualHeading: "أدلة الآلات",
        manualDescription:
            "استورد دليلاً بصيغة PDF نصية أو TXT. تتم المعالجة والبحث محلياً.",
        selectManualText: "اختر دليلاً محلياً",
        manualTypesText: "PDF أو TXT، بحد أقصى 25 ميغابايت",
        noFileSelected: "لم يتم اختيار ملف",
        importManual: "استيراد الدليل",
        importingManual: "جارٍ الاستيراد محلياً...",
        documentSingle: "مستند",
        documentPlural: "مستندات",
        chunkSingle: "قسم قابل للبحث",
        chunkPlural: "أقسام قابلة للبحث",
        documentsEmptyTitle: "لا توجد أدلة محلية مستوردة",
        documentsEmptyText:
            "يمكن لـ Siyana AI تقديم إرشادات عامة دون دليل.",
        importedSuccessfully: "تم استيراد المستند محلياً.",
        deleteDocument: "حذف",
        deleteConfirmation:
            "هل تريد حذف هذا الدليل المحلي وجميع أقسامه المفهرسة؟",
        documentDeleted: "تم حذف المستند محلياً.",
        pages: "صفحات",
        sections: "أقسام",
        fileSize: "الحجم",
        importDate: "تاريخ الاستيراد",

        questionHeading: "صف الحالة",
        questionHelp:
            "أضف معلومات الآلة المتوفرة، ولا تدخل بيانات شخصية أو سرية.",
        languageLabel: "اللغة",
        machineNameLabel: "الآلة أو المعدة",
        machineNamePlaceholder: "مثال: مكبس هوائي",
        machineModelLabel: "الطراز، إذا كان معروفاً",
        machineModelPlaceholder: "مثال: PX-200",
        questionLabel: "العَرَض أو السؤال",
        questionPlaceholder:
            "مثال: أصبحت الأسطوانة الهوائية بطيئة في الاتجاهين.",
        contextLabel: "سياق إضافي، إذا كان متوفراً",
        contextPlaceholder:
            "الحمل، نص الإنذار، التغييرات الأخيرة، الملاحظات...",

        useDocumentsTitle: "البحث في الأدلة المحلية",
        useDocumentsText:
            "استخدام المقاطع المحلية ذات الصلة وإظهار المصادر.",
        maximumSourcesLabel: "الحد الأقصى للمصادر",

        safetyReminderTitle: "تذكير بالسلامة",
        safetyReminderText:
            "أوقف الآلة واعزل مصادر الطاقة الخطرة قبل الفحص أو الصيانة.",

        submitButton: "اسأل Siyana AI",
        submitting: "جارٍ إنشاء الإجابة محلياً...",

        emptyTitle: "المساعد المحلي جاهز",
        emptyText:
            "أرسل سؤالاً عن الصيانة الصناعية لعرض إجابة منظمة.",

        answerTitle: "إرشادات أولية",
        copy: "نسخ",
        copied: "تم النسخ",
        important: "مهم",
        errorTitle: "تعذر إتمام العملية",
        genericError:
            "تعذر على التطبيق المحلي إتمام هذه العملية. تحقق من نافذة الخلفية.",

        modelLabel: "النموذج",
        durationLabel: "المدة",
        offlineLabel: "استدلال دون إنترنت",
        retrievalUsed: "تم استخدام الأدلة المحلية",
        retrievalNotUsed: "لم يتم العثور على مصدر محلي مناسب",

        citationsTitle: "المقاطع المسترجعة من الأدلة",
        sourceSingle: "مصدر",
        sourcePlural: "مصادر",
        page: "الصفحة",

        limitationsTitle: "إمكانات النموذج الأولي الحالي",
        capabilityOneTitle: "ذكاء اصطناعي محلي متعدد اللغات",
        capabilityOneText:
            "إرشادات بالإنجليزية والفرنسية والعربية باستخدام Qwen3-4B.",
        capabilityTwoTitle: "الاستناد إلى الأدلة المحلية",
        capabilityTwoText:
            "البحث في أدلة PDF وTXT باستخدام SQLite FTS5.",
        capabilityThreeTitle: "التركيز على السلامة",
        capabilityThreeText:
            "يرفض تجاوز أنظمة الأمان وإجراءات الصيانة الخطرة."
    }
};


const elements = {
    root: document.documentElement,

    statusBadge: document.getElementById("statusBadge"),
    statusText: document.getElementById("statusText"),

    language: document.getElementById("language"),

    manualFile: document.getElementById("manualFile"),
    selectedFilename: document.getElementById("selectedFilename"),
    importManualButton: document.getElementById("importManualButton"),
    importManualButtonText:
        document.getElementById("importManualButtonText"),
    manualSpinner: document.getElementById("manualSpinner"),
    manualMessage: document.getElementById("manualMessage"),
    documentList: document.getElementById("documentList"),
    documentsEmptyState:
        document.getElementById("documentsEmptyState"),
    documentCount: document.getElementById("documentCount"),
    chunkCount: document.getElementById("chunkCount"),

    chatForm: document.getElementById("chatForm"),
    machineName: document.getElementById("machineName"),
    machineModel: document.getElementById("machineModel"),
    question: document.getElementById("question"),
    additionalContext:
        document.getElementById("additionalContext"),
    useDocuments: document.getElementById("useDocuments"),
    maximumSources: document.getElementById("maximumSources"),
    characterCount: document.getElementById("characterCount"),

    submitButton: document.getElementById("submitButton"),
    submitButtonText:
        document.getElementById("submitButtonText"),
    buttonSpinner: document.getElementById("buttonSpinner"),

    emptyState: document.getElementById("emptyState"),
    answerContent: document.getElementById("answerContent"),
    errorPanel: document.getElementById("errorPanel"),
    errorText: document.getElementById("errorText"),

    answerText: document.getElementById("answerText"),
    answerSafetyNotice:
        document.getElementById("answerSafetyNotice"),

    modelMetadata: document.getElementById("modelMetadata"),
    durationMetadata:
        document.getElementById("durationMetadata"),
    offlineMetadata:
        document.getElementById("offlineMetadata"),
    retrievalMetadata:
        document.getElementById("retrievalMetadata"),

    citationsSection:
        document.getElementById("citationsSection"),
    citationsTitle:
        document.getElementById("citationsTitle"),
    citationCount:
        document.getElementById("citationCount"),
    citationList:
        document.getElementById("citationList"),

    copyButton: document.getElementById("copyButton")
};


const textBindings = {
    brandSubtitle: "brandSubtitle",
    heroTitle: "heroTitle",
    heroDescription: "heroDescription",
    privacyTitle: "privacyTitle",
    privacyText: "privacyText",

    manualHeading: "manualHeading",
    manualDescription: "manualDescription",
    selectManualText: "selectManualText",
    manualTypesText: "manualTypesText",
    documentsEmptyTitle: "documentsEmptyTitle",
    documentsEmptyText: "documentsEmptyText",

    questionHeading: "questionHeading",
    questionHelp: "questionHelp",
    languageLabel: "languageLabel",
    machineNameLabel: "machineNameLabel",
    machineModelLabel: "machineModelLabel",
    questionLabel: "questionLabel",
    contextLabel: "contextLabel",

    useDocumentsTitle: "useDocumentsTitle",
    useDocumentsText: "useDocumentsText",
    maximumSourcesLabel: "maximumSourcesLabel",

    safetyReminderTitle: "safetyReminderTitle",
    safetyReminderText: "safetyReminderText",

    emptyTitle: "emptyTitle",
    emptyText: "emptyText",
    answerTitle: "answerTitle",
    answerSafetyTitle: "important",
    errorTitle: "errorTitle",

    limitationsTitle: "limitationsTitle",
    capabilityOneTitle: "capabilityOneTitle",
    capabilityOneText: "capabilityOneText",
    capabilityTwoTitle: "capabilityTwoTitle",
    capabilityTwoText: "capabilityTwoText",
    capabilityThreeTitle: "capabilityThreeTitle",
    capabilityThreeText: "capabilityThreeText"
};


let documentsCache = [];


function currentLanguage() {
    return elements.language.value;
}


function strings() {
    return translations[currentLanguage()];
}


function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function formatFileSize(bytes) {
    const value = Number(bytes);

    if (!Number.isFinite(value) || value < 0) {
        return "—";
    }

    if (value < 1024) {
        return `${value} B`;
    }

    if (value < 1024 * 1024) {
        return `${(value / 1024).toFixed(1)} KB`;
    }

    return `${(value / (1024 * 1024)).toFixed(2)} MB`;
}


function formatDate(value) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return new Intl.DateTimeFormat(
        currentLanguage(),
        {
            dateStyle: "medium",
            timeStyle: "short"
        }
    ).format(date);
}


function applyLanguage(language) {
    const translation = translations[language];

    document.title = translation.documentTitle;

    elements.root.lang = language;
    elements.root.dir = language === "ar" ? "rtl" : "ltr";

    for (const [elementId, translationKey] of Object.entries(textBindings)) {
        const element = document.getElementById(elementId);

        if (element) {
            element.textContent = translation[translationKey];
        }
    }

    elements.machineName.placeholder =
        translation.machineNamePlaceholder;

    elements.machineModel.placeholder =
        translation.machineModelPlaceholder;

    elements.question.placeholder =
        translation.questionPlaceholder;

    elements.additionalContext.placeholder =
        translation.contextPlaceholder;

    elements.copyButton.textContent = translation.copy;

    if (!elements.importManualButton.disabled) {
        elements.importManualButtonText.textContent =
            translation.importManual;
    }

    if (!elements.submitButton.disabled) {
        elements.submitButtonText.textContent =
            translation.submitButton;
    }

    if (!elements.manualFile.files.length) {
        elements.selectedFilename.textContent =
            translation.noFileSelected;
    }

    updateCharacterCount();
    renderDocuments(documentsCache);
    checkHealth();
}


function setStatus(state, message) {
    elements.statusBadge.classList.remove(
        "status-checking",
        "status-ready",
        "status-error"
    );

    elements.statusBadge.classList.add(`status-${state}`);
    elements.statusText.textContent = message;
}


async function checkHealth() {
    const translation = strings();

    setStatus("checking", translation.statusChecking);

    try {
        const response = await fetch("/api/health", {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error(`Health request failed: ${response.status}`);
        }

        const data = await response.json();

        if (
            data.application === "ready" &&
            data.model_server === "ready" &&
            data.model_file_exists === true
        ) {
            setStatus("ready", translation.statusReady);
        } else {
            setStatus("error", translation.statusUnavailable);
        }
    } catch (error) {
        console.error(error);
        setStatus("error", translation.statusUnavailable);
    }
}


function updateCharacterCount() {
    elements.characterCount.textContent =
        `${elements.question.value.length} / 4000`;
}


function setChatLoading(loading) {
    const translation = strings();

    elements.submitButton.disabled = loading;
    elements.buttonSpinner.hidden = !loading;

    elements.submitButtonText.textContent = loading
        ? translation.submitting
        : translation.submitButton;
}


function setManualLoading(loading) {
    const translation = strings();

    elements.importManualButton.disabled =
        loading || !elements.manualFile.files.length;

    elements.manualSpinner.hidden = !loading;

    elements.importManualButtonText.textContent = loading
        ? translation.importingManual
        : translation.importManual;
}


function showManualMessage(message, state = "success") {
    elements.manualMessage.hidden = false;
    elements.manualMessage.textContent = message;

    elements.manualMessage.classList.remove(
        "manual-message-success",
        "manual-message-error"
    );

    elements.manualMessage.classList.add(
        state === "error"
            ? "manual-message-error"
            : "manual-message-success"
    );
}


function clearManualMessage() {
    elements.manualMessage.hidden = true;
    elements.manualMessage.textContent = "";
}


async function loadDocuments() {
    try {
        const response = await fetch("/api/documents", {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error(`Document request failed: ${response.status}`);
        }

        const data = await response.json();

        documentsCache = Array.isArray(data.documents)
            ? data.documents
            : [];

        renderDocuments(documentsCache);

        const translation = strings();

        elements.documentCount.textContent =
            `${data.document_count} ${
                data.document_count === 1
                    ? translation.documentSingle
                    : translation.documentPlural
            }`;

        elements.chunkCount.textContent =
            `${data.chunk_count} ${
                data.chunk_count === 1
                    ? translation.chunkSingle
                    : translation.chunkPlural
            }`;
    } catch (error) {
        console.error(error);
        showManualMessage(strings().genericError, "error");
    }
}


function renderDocuments(documents) {
    const translation = strings();

    elements.documentList.innerHTML = "";

    if (!documents.length) {
        const empty = document.createElement("div");
        empty.className = "documents-empty";

        const title = document.createElement("strong");
        title.textContent = translation.documentsEmptyTitle;

        const text = document.createElement("p");
        text.textContent = translation.documentsEmptyText;

        empty.append(title, text);
        elements.documentList.appendChild(empty);

        return;
    }

    for (const documentItem of documents) {
        const card = document.createElement("article");
        card.className = "document-card";

        card.innerHTML = `
            <div class="document-icon">
                ${escapeHtml(documentItem.file_type.toUpperCase().replace(".", ""))}
            </div>

            <div class="document-details">
                <strong title="${escapeHtml(documentItem.filename)}">
                    ${escapeHtml(documentItem.filename)}
                </strong>

                <div class="document-meta">
                    <span>
                        ${documentItem.page_count} ${escapeHtml(translation.pages)}
                    </span>

                    <span>
                        ${documentItem.chunk_count} ${escapeHtml(translation.sections)}
                    </span>

                    <span>
                        ${escapeHtml(translation.fileSize)}:
                        ${escapeHtml(formatFileSize(documentItem.file_size_bytes))}
                    </span>
                </div>

                <small>
                    ${escapeHtml(translation.importDate)}:
                    ${escapeHtml(formatDate(documentItem.imported_at))}
                </small>
            </div>

            <button
                class="delete-document-button"
                type="button"
                data-document-id="${documentItem.id}"
                data-filename="${escapeHtml(documentItem.filename)}"
            >
                ${escapeHtml(translation.deleteDocument)}
            </button>
        `;

        elements.documentList.appendChild(card);
    }

    const deleteButtons =
        elements.documentList.querySelectorAll(
            ".delete-document-button"
        );

    for (const button of deleteButtons) {
        button.addEventListener("click", () => {
            deleteDocument(
                Number(button.dataset.documentId),
                button.dataset.filename || ""
            );
        });
    }
}


async function importManual() {
    const file = elements.manualFile.files[0];

    if (!file) {
        return;
    }

    clearManualMessage();
    setManualLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(
            "/api/documents/import",
            {
                method: "POST",
                body: formData
            }
        );

        let data = null;

        try {
            data = await response.json();
        } catch {
            data = null;
        }

        if (!response.ok) {
            const message =
                data && typeof data.detail === "string"
                    ? data.detail
                    : strings().genericError;

            throw new Error(message);
        }

        showManualMessage(
            strings().importedSuccessfully,
            "success"
        );

        elements.manualFile.value = "";
        elements.selectedFilename.textContent =
            strings().noFileSelected;

        await loadDocuments();
    } catch (error) {
        console.error(error);

        showManualMessage(
            error instanceof Error
                ? error.message
                : strings().genericError,
            "error"
        );
    } finally {
        setManualLoading(false);
    }
}


async function deleteDocument(documentId, filename) {
    const translation = strings();

    const confirmed = window.confirm(
        `${translation.deleteConfirmation}\n\n${filename}`
    );

    if (!confirmed) {
        return;
    }

    clearManualMessage();

    try {
        const response = await fetch(
            `/api/documents/${documentId}`,
            {
                method: "DELETE"
            }
        );

        let data = null;

        try {
            data = await response.json();
        } catch {
            data = null;
        }

        if (!response.ok) {
            const message =
                data && typeof data.detail === "string"
                    ? data.detail
                    : translation.genericError;

            throw new Error(message);
        }

        showManualMessage(
            translation.documentDeleted,
            "success"
        );

        await loadDocuments();
    } catch (error) {
        console.error(error);

        showManualMessage(
            error instanceof Error
                ? error.message
                : translation.genericError,
            "error"
        );
    }
}


function showEmptyState() {
    elements.emptyState.hidden = false;
    elements.answerContent.hidden = true;
    elements.errorPanel.hidden = true;
}


function showError(message) {
    elements.emptyState.hidden = true;
    elements.answerContent.hidden = true;
    elements.errorPanel.hidden = false;
    elements.errorText.textContent = message;
}


function renderCitations(citations) {
    const translation = strings();

    elements.citationList.innerHTML = "";

    if (!Array.isArray(citations) || !citations.length) {
        elements.citationsSection.hidden = true;
        return;
    }

    elements.citationsSection.hidden = false;

    elements.citationCount.textContent =
        `${citations.length} ${
            citations.length === 1
                ? translation.sourceSingle
                : translation.sourcePlural
        }`;

    for (const citation of citations) {
        const card = document.createElement("article");
        card.className = "citation-card";

        const header = document.createElement("div");
        header.className = "citation-card-header";

        const sourceNumber = document.createElement("span");
        sourceNumber.className = "citation-number";
        sourceNumber.textContent = `[SOURCE ${citation.number}]`;

        const sourceLocation = document.createElement("span");
        sourceLocation.className = "citation-location";
        sourceLocation.textContent =
            `${citation.filename} • ${translation.page} ${citation.page_number}`;

        header.append(sourceNumber, sourceLocation);

        const excerpt = document.createElement("p");
        excerpt.textContent = citation.excerpt;

        card.append(header, excerpt);
        elements.citationList.appendChild(card);
    }
}


function showAnswer(data) {
    const translation = strings();

    elements.emptyState.hidden = true;
    elements.errorPanel.hidden = true;
    elements.answerContent.hidden = false;

    elements.answerText.textContent = data.answer;
    elements.answerSafetyNotice.textContent =
        data.safety_notice;

    elements.modelMetadata.textContent =
        `${translation.modelLabel}: ${data.model}`;

    elements.durationMetadata.textContent =
        `${translation.durationLabel}: ${data.duration_seconds} s`;

    elements.offlineMetadata.textContent =
        `${translation.offlineLabel}: ${data.offline ? "✓" : "—"}`;

    elements.retrievalMetadata.textContent =
        data.document_search_used
            ? `${translation.retrievalUsed}: ${data.source_count}`
            : translation.retrievalNotUsed;

    renderCitations(data.citations);
}


async function submitQuestion(event) {
    event.preventDefault();

    const translation = strings();
    const question = elements.question.value.trim();

    if (question.length < 3) {
        showError(translation.genericError);
        return;
    }

    setChatLoading(true);
    elements.errorPanel.hidden = true;

    const payload = {
        language: currentLanguage(),
        question,
        machine_name: elements.machineName.value.trim(),
        machine_model: elements.machineModel.value.trim(),
        additional_context:
            elements.additionalContext.value.trim(),
        use_documents: elements.useDocuments.checked,
        maximum_sources: Number(elements.maximumSources.value)
    };

    try {
        const response = await fetch(
            "/api/chat-grounded",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body: JSON.stringify(payload)
            }
        );

        let data = null;

        try {
            data = await response.json();
        } catch {
            data = null;
        }

        if (!response.ok) {
            const message =
                data && typeof data.detail === "string"
                    ? data.detail
                    : translation.genericError;

            throw new Error(message);
        }

        showAnswer(data);
    } catch (error) {
        console.error(error);

        showError(
            error instanceof Error
                ? error.message
                : translation.genericError
        );
    } finally {
        setChatLoading(false);
    }
}


async function copyAnswer() {
    const answer = elements.answerText.textContent;

    if (!answer) {
        return;
    }

    try {
        await navigator.clipboard.writeText(answer);

        elements.copyButton.textContent = strings().copied;

        window.setTimeout(() => {
            elements.copyButton.textContent = strings().copy;
        }, 1400);
    } catch (error) {
        console.error("Unable to copy response:", error);
    }
}


elements.language.addEventListener("change", () => {
    applyLanguage(currentLanguage());
});

elements.question.addEventListener(
    "input",
    updateCharacterCount
);

elements.manualFile.addEventListener("change", () => {
    clearManualMessage();

    const file = elements.manualFile.files[0];

    elements.selectedFilename.textContent = file
        ? file.name
        : strings().noFileSelected;

    elements.importManualButton.disabled = !file;
});

elements.importManualButton.addEventListener(
    "click",
    importManual
);

elements.chatForm.addEventListener(
    "submit",
    submitQuestion
);

elements.copyButton.addEventListener(
    "click",
    copyAnswer
);


showEmptyState();
applyLanguage("en");
loadDocuments();
checkHealth();

window.setInterval(checkHealth, 30000);