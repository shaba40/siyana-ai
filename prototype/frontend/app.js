"use strict";

/*
 * Siyana AI Phase 4A frontend.
 *
 * Responsibilities:
 * - Check the local application and model status.
 * - Switch the interface language.
 * - Submit questions to the local FastAPI backend.
 * - Display the generated response and metadata.
 * - Support right-to-left Arabic presentation.
 * - Copy responses to the clipboard.
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
            "Describe an industrial-machine symptom. Siyana AI uses the local Qwen3-4B model to produce structured, safety-focused preliminary guidance.",
        privacyTitle: "Local processing",
        privacyText:
            "Questions and answers remain on this computer. No cloud inference API is used.",
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
            "The local application could not generate a response. Check the backend terminal and try again.",
        modelLabel: "Model",
        durationLabel: "Duration",
        offlineLabel: "Offline inference",
        limitationsTitle: "Current prototype capabilities",
        capabilityOneTitle: "Available now",
        capabilityOneText:
            "Local English, French and Arabic maintenance guidance.",
        capabilityTwoTitle: "Safety focused",
        capabilityTwoText:
            "Refuses guard bypasses and energized maintenance instructions.",
        capabilityThreeTitle: "Coming next",
        capabilityThreeText:
            "Local machine-manual import, search and citations."
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
            "Décrivez le symptôme d'une machine industrielle. Siyana AI utilise le modèle local Qwen3-4B pour produire des conseils préliminaires structurés et axés sur la sécurité.",
        privacyTitle: "Traitement local",
        privacyText:
            "Les questions et les réponses restent sur cet ordinateur. Aucune API d'inférence cloud n'est utilisée.",
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
        safetyReminderTitle: "Rappel de sécurité",
        safetyReminderText:
            "Arrêtez la machine et isolez les énergies dangereuses avant toute inspection ou maintenance.",
        submitButton: "Interroger Siyana AI",
        submitting: "Génération locale...",
        emptyTitle: "L'assistant local est prêt",
        emptyText:
            "Envoyez une question de maintenance industrielle pour afficher une réponse structurée.",
        answerTitle: "Conseils préliminaires",
        copy: "Copier",
        copied: "Copié",
        important: "Important",
        errorTitle: "Impossible de générer une réponse",
        genericError:
            "L'application locale n'a pas pu générer une réponse. Vérifiez le terminal du backend et réessayez.",
        modelLabel: "Modèle",
        durationLabel: "Durée",
        offlineLabel: "Inférence hors ligne",
        limitationsTitle: "Fonctions du prototype actuel",
        capabilityOneTitle: "Disponible maintenant",
        capabilityOneText:
            "Conseils locaux en anglais, français et arabe.",
        capabilityTwoTitle: "Axé sur la sécurité",
        capabilityTwoText:
            "Refuse le contournement des protecteurs et les interventions sous tension.",
        capabilityThreeTitle: "Prochaine étape",
        capabilityThreeText:
            "Importation locale de manuels, recherche et citations."
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
            "صف عَرَضاً متعلقاً بآلة صناعية. يستخدم Siyana AI نموذج Qwen3-4B المحلي لتقديم إرشادات أولية منظمة تركز على السلامة.",
        privacyTitle: "معالجة محلية",
        privacyText:
            "تبقى الأسئلة والإجابات على هذا الحاسوب، ولا تستخدم أي خدمة سحابية للاستدلال.",
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
        errorTitle: "تعذر إنشاء الإجابة",
        genericError:
            "تعذر على التطبيق المحلي إنشاء إجابة. تحقق من نافذة الخلفية ثم حاول مرة أخرى.",
        modelLabel: "النموذج",
        durationLabel: "المدة",
        offlineLabel: "استدلال دون إنترنت",
        limitationsTitle: "إمكانات النموذج الأولي الحالي",
        capabilityOneTitle: "متوفر الآن",
        capabilityOneText:
            "إرشادات محلية للصيانة بالإنجليزية والفرنسية والعربية.",
        capabilityTwoTitle: "يركز على السلامة",
        capabilityTwoText:
            "يرفض تجاوز الحواجز وتعليمات الصيانة تحت الجهد.",
        capabilityThreeTitle: "الخطوة التالية",
        capabilityThreeText:
            "استيراد أدلة الآلات محلياً والبحث فيها وإظهار المصادر."
    }
};


const elements = {
    document: document.documentElement,

    statusBadge: document.getElementById("statusBadge"),
    statusText: document.getElementById("statusText"),

    language: document.getElementById("language"),
    chatForm: document.getElementById("chatForm"),

    machineName: document.getElementById("machineName"),
    machineModel: document.getElementById("machineModel"),
    question: document.getElementById("question"),
    additionalContext: document.getElementById("additionalContext"),

    characterCount: document.getElementById("characterCount"),

    submitButton: document.getElementById("submitButton"),
    submitButtonText: document.getElementById("submitButtonText"),
    buttonSpinner: document.getElementById("buttonSpinner"),

    emptyState: document.getElementById("emptyState"),
    answerContent: document.getElementById("answerContent"),
    errorPanel: document.getElementById("errorPanel"),

    answerText: document.getElementById("answerText"),
    answerSafetyNotice: document.getElementById("answerSafetyNotice"),

    modelMetadata: document.getElementById("modelMetadata"),
    durationMetadata: document.getElementById("durationMetadata"),
    offlineMetadata: document.getElementById("offlineMetadata"),

    copyButton: document.getElementById("copyButton"),
    errorText: document.getElementById("errorText")
};


const textBindings = {
    brandSubtitle: "brandSubtitle",
    heroTitle: "heroTitle",
    heroDescription: "heroDescription",
    privacyTitle: "privacyTitle",
    privacyText: "privacyText",
    questionHeading: "questionHeading",
    questionHelp: "questionHelp",
    languageLabel: "languageLabel",
    machineNameLabel: "machineNameLabel",
    machineModelLabel: "machineModelLabel",
    questionLabel: "questionLabel",
    contextLabel: "contextLabel",
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


function currentLanguage() {
    return elements.language.value;
}


function currentTranslations() {
    return translations[currentLanguage()];
}


function applyLanguage(language) {
    const strings = translations[language];

    document.title = strings.documentTitle;

    elements.document.lang = language;
    elements.document.dir = language === "ar" ? "rtl" : "ltr";

    for (const [elementId, translationKey] of Object.entries(textBindings)) {
        const element = document.getElementById(elementId);

        if (element) {
            element.textContent = strings[translationKey];
        }
    }

    elements.machineName.placeholder = strings.machineNamePlaceholder;
    elements.machineModel.placeholder = strings.machineModelPlaceholder;
    elements.question.placeholder = strings.questionPlaceholder;
    elements.additionalContext.placeholder = strings.contextPlaceholder;

    elements.copyButton.textContent = strings.copy;

    if (!elements.submitButton.disabled) {
        elements.submitButtonText.textContent = strings.submitButton;
    }

    updateCharacterCount();
    checkHealth();
}


function updateCharacterCount() {
    const count = elements.question.value.length;

    elements.characterCount.textContent = `${count} / 4000`;
}


function setStatus(state, text) {
    elements.statusBadge.classList.remove(
        "status-checking",
        "status-ready",
        "status-error"
    );

    elements.statusBadge.classList.add(`status-${state}`);
    elements.statusText.textContent = text;
}


async function checkHealth() {
    const strings = currentTranslations();

    setStatus("checking", strings.statusChecking);

    try {
        const response = await fetch("/api/health", {
            method: "GET",
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
            setStatus("ready", strings.statusReady);
            return;
        }

        setStatus("error", strings.statusUnavailable);
    } catch (error) {
        console.error(error);
        setStatus("error", strings.statusUnavailable);
    }
}


function setLoading(loading) {
    const strings = currentTranslations();

    elements.submitButton.disabled = loading;
    elements.buttonSpinner.hidden = !loading;

    elements.submitButtonText.textContent = loading
        ? strings.submitting
        : strings.submitButton;
}


function showEmptyState() {
    elements.emptyState.hidden = false;
    elements.answerContent.hidden = true;
    elements.errorPanel.hidden = true;
}


function showAnswer(data) {
    const strings = currentTranslations();

    elements.emptyState.hidden = true;
    elements.errorPanel.hidden = true;
    elements.answerContent.hidden = false;

    elements.answerText.textContent = data.answer;
    elements.answerSafetyNotice.textContent = data.safety_notice;

    elements.modelMetadata.textContent =
        `${strings.modelLabel}: ${data.model}`;

    elements.durationMetadata.textContent =
        `${strings.durationLabel}: ${data.duration_seconds} s`;

    elements.offlineMetadata.textContent =
        `${strings.offlineLabel}: ${data.offline ? "✓" : "—"}`;
}


function showError(message) {
    elements.emptyState.hidden = true;
    elements.answerContent.hidden = true;
    elements.errorPanel.hidden = false;

    elements.errorText.textContent = message;
}


async function submitQuestion(event) {
    event.preventDefault();

    const strings = currentTranslations();
    const question = elements.question.value.trim();

    if (question.length < 3) {
        showError(strings.genericError);
        return;
    }

    setLoading(true);
    elements.errorPanel.hidden = true;

    const payload = {
        language: currentLanguage(),
        question,
        machine_name: elements.machineName.value.trim(),
        machine_model: elements.machineModel.value.trim(),
        additional_context: elements.additionalContext.value.trim()
    };

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(payload)
        });

        let data = null;

        try {
            data = await response.json();
        } catch {
            data = null;
        }

        if (!response.ok) {
            const detail =
                data && typeof data.detail === "string"
                    ? data.detail
                    : strings.genericError;

            throw new Error(detail);
        }

        showAnswer(data);
    } catch (error) {
        console.error(error);

        const message =
            error instanceof Error && error.message
                ? error.message
                : strings.genericError;

        showError(message);
    } finally {
        setLoading(false);
    }
}


async function copyAnswer() {
    const strings = currentTranslations();
    const answer = elements.answerText.textContent;

    if (!answer) {
        return;
    }

    try {
        await navigator.clipboard.writeText(answer);

        elements.copyButton.textContent = strings.copied;

        window.setTimeout(() => {
            elements.copyButton.textContent =
                currentTranslations().copy;
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
checkHealth();

window.setInterval(checkHealth, 30000);
