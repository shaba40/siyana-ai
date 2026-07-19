"use strict";

/*
 * Siyana AI — Sprint 1 UX enhancements
 *
 * This file adds:
 * - Task modes
 * - Quick-start scenarios
 * - Honest request stages
 * - Elapsed generation timer
 * - Safety classification after generation
 *
 * It does not change backend API contracts.
 */

(() => {
    const byId = (id) => document.getElementById(id);

    const elements = {
        language: byId("language"),
        chatForm: byId("chatForm"),
        question: byId("question"),
        machineName: byId("machineName"),
        machineModel: byId("machineModel"),
        additionalContext: byId("additionalContext"),
        useDocuments: byId("useDocuments"),
        submitButton: byId("submitButton"),
        answerContent: byId("answerContent"),
        answerText: byId("answerText"),
        citationsSection: byId("citationsSection"),
        errorPanel: byId("errorPanel"),

        taskMode: byId("taskMode"),
        scenarioList: byId("scenarioList"),

        progressPanel: byId("progressPanel"),
        progressTitle: byId("progressTitle"),
        progressMessage: byId("progressMessage"),
        progressTimer: byId("progressTimer"),
        progressStages: byId("progressStages"),

        safetyState: byId("safetyState"),
        safetyStateLabel: byId("safetyStateLabel"),
        safetyStateText: byId("safetyStateText")
    };

    const requiredElements = [
        "language",
        "chatForm",
        "question",
        "machineName",
        "machineModel",
        "additionalContext",
        "useDocuments",
        "submitButton",
        "answerContent",
        "answerText",
        "errorPanel",
        "taskMode",
        "scenarioList",
        "progressPanel",
        "progressTitle",
        "progressMessage",
        "progressTimer",
        "progressStages",
        "safetyState",
        "safetyStateLabel",
        "safetyStateText"
    ];

    const missingElements = requiredElements.filter(
        (name) => !elements[name]
    );

    if (missingElements.length > 0) {
        console.error(
            "Sprint 1 could not start. Missing elements:",
            missingElements
        );

        return;
    }

    const translations = {
        en: {
            progressTitle: "Working locally",
            preparing: "Preparing the maintenance request…",
            searching: "Searching relevant local manual sections…",
            generating: "Generating preliminary guidance on this computer…",
            structuring: "Structuring the final guidance…",
            seconds: "seconds",

            safetyGeneral: "GENERAL GUIDANCE",
            safetyGeneralText:
                "Review the guidance and verify equipment-specific information.",

            safetyCaution: "CAUTION",
            safetyCautionText:
                "The response contains important precautions or unresolved uncertainty.",

            safetyStop: "STOP WORK",
            safetyStopText:
                "The response identifies a condition that requires keeping the equipment out of service.",

            safetyEscalate: "ESCALATION REQUIRED",
            safetyEscalateText:
                "The condition should be reviewed by qualified and authorized personnel."
        },

        fr: {
            progressTitle: "Traitement local",
            preparing: "Préparation de la demande de maintenance…",
            searching: "Recherche dans les sections pertinentes des manuels locaux…",
            generating: "Génération des conseils préliminaires sur cet ordinateur…",
            structuring: "Structuration des conseils finaux…",
            seconds: "secondes",

            safetyGeneral: "CONSEILS GÉNÉRAUX",
            safetyGeneralText:
                "Vérifiez les informations propres à l'équipement avant toute intervention.",

            safetyCaution: "ATTENTION",
            safetyCautionText:
                "La réponse contient des précautions importantes ou une incertitude non résolue.",

            safetyStop: "ARRÊT DU TRAVAIL",
            safetyStopText:
                "La réponse identifie une condition exigeant de maintenir l'équipement hors service.",

            safetyEscalate: "ESCALADE REQUISE",
            safetyEscalateText:
                "La situation doit être examinée par du personnel qualifié et autorisé."
        },

        ar: {
            progressTitle: "المعالجة المحلية",
            preparing: "جارٍ إعداد طلب الصيانة…",
            searching: "جارٍ البحث في الأقسام المناسبة من الأدلة المحلية…",
            generating: "جارٍ إنشاء الإرشادات الأولية على هذا الحاسوب…",
            structuring: "جارٍ تنظيم الإرشادات النهائية…",
            seconds: "ثانية",

            safetyGeneral: "إرشادات عامة",
            safetyGeneralText:
                "تحقق من المعلومات الخاصة بالمعدة قبل أي تدخل.",

            safetyCaution: "تنبيه",
            safetyCautionText:
                "تتضمن الإجابة احتياطات مهمة أو معلومات غير محسومة.",

            safetyStop: "إيقاف العمل",
            safetyStopText:
                "تشير الإجابة إلى حالة تتطلب إبقاء المعدة خارج الخدمة.",

            safetyEscalate: "يلزم التصعيد",
            safetyEscalateText:
                "يجب إحالة الحالة إلى أشخاص مؤهلين ومصرح لهم."
        }
    };

    const scenarios = [
        {
            id: "motor-overheating",
            icon: "M",
            title: {
                en: "Motor overheating",
                fr: "Surchauffe du moteur",
                ar: "ارتفاع حرارة المحرك"
            },
            equipment: {
                en: "Industrial electric motor",
                fr: "Moteur électrique industriel",
                ar: "محرك كهربائي صناعي"
            },
            question: {
                en:
                    "The electric motor becomes unusually hot after ten minutes of operation. What are the possible causes, safe preliminary checks, stop-work conditions, and information required?",
                fr:
                    "Le moteur électrique devient anormalement chaud après dix minutes de fonctionnement. Quelles sont les causes possibles, les vérifications préliminaires sûres, les conditions d'arrêt et les informations nécessaires ?",
                ar:
                    "ترتفع حرارة المحرك الكهربائي بصورة غير طبيعية بعد عشر دقائق من التشغيل. ما الأسباب المحتملة والفحوصات الأولية الآمنة وحالات إيقاف العمل والمعلومات المطلوبة؟"
            }
        },
        {
            id: "pneumatic-cylinder",
            icon: "P",
            title: {
                en: "Slow pneumatic cylinder",
                fr: "Vérin pneumatique lent",
                ar: "أسطوانة هوائية بطيئة"
            },
            equipment: {
                en: "Pneumatic production machine",
                fr: "Machine de production pneumatique",
                ar: "آلة إنتاج تعمل بالهواء المضغوط"
            },
            question: {
                en:
                    "The pneumatic cylinder is slow in both directions. What should the technician check safely?",
                fr:
                    "Le vérin pneumatique est lent dans les deux sens. Quelles vérifications sûres le technicien doit-il effectuer ?",
                ar:
                    "الأسطوانة الهوائية بطيئة في الاتجاهين. ما الفحوصات الآمنة التي يجب على الفني القيام بها؟"
            }
        },
        {
            id: "conveyor-vibration",
            icon: "C",
            title: {
                en: "Conveyor vibration",
                fr: "Vibration du convoyeur",
                ar: "اهتزاز الناقل"
            },
            equipment: {
                en: "Industrial belt conveyor",
                fr: "Convoyeur industriel à bande",
                ar: "ناقل صناعي بالحزام"
            },
            question: {
                en:
                    "The conveyor vibrates more than usual and intermittently produces a metallic noise. Provide a safe preliminary troubleshooting plan.",
                fr:
                    "Le convoyeur vibre plus que d'habitude et produit par intermittence un bruit métallique. Proposez un plan préliminaire et sûr de recherche de panne.",
                ar:
                    "يهتز الناقل أكثر من المعتاد ويصدر صوتاً معدنياً متقطعاً. قدم خطة أولية آمنة للبحث عن سبب العطل."
            }
        },
        {
            id: "unknown-alarm",
            icon: "E",
            title: {
                en: "Unknown alarm code",
                fr: "Code d'alarme inconnu",
                ar: "رمز إنذار غير معروف"
            },
            equipment: {
                en: "Industrial production machine",
                fr: "Machine de production industrielle",
                ar: "آلة إنتاج صناعية"
            },
            question: {
                en:
                    "The machine displays alarm E07. What information is required before identifying the fault or recommending a repair?",
                fr:
                    "La machine affiche l'alarme E07. Quelles informations sont nécessaires avant d'identifier la panne ou de recommander une réparation ?",
                ar:
                    "تعرض الآلة رمز الإنذار E07. ما المعلومات المطلوبة قبل تحديد العطل أو اقتراح الإصلاح؟"
            }
        },
        {
            id: "safety-device",
            icon: "S",
            title: {
                en: "Safety-device failure",
                fr: "Défaillance de sécurité",
                ar: "عطل في جهاز أمان"
            },
            equipment: {
                en: "Industrial production machine",
                fr: "Machine de production industrielle",
                ar: "آلة إنتاج صناعية"
            },
            question: {
                en:
                    "The emergency-stop button is damaged, but production wants to continue. What is the safe response?",
                fr:
                    "Le bouton d'arrêt d'urgence est endommagé, mais la production souhaite continuer. Quelle est la réponse sûre ?",
                ar:
                    "زر التوقف الاضطراري تالف، لكن الإنتاج يريد الاستمرار. ما الإجراء الآمن؟"
            }
        },
        {
            id: "shift-handover",
            icon: "H",
            title: {
                en: "Shift handover",
                fr: "Passation de poste",
                ar: "تسليم المناوبة"
            },
            equipment: {
                en: "Production machine",
                fr: "Machine de production",
                ar: "آلة إنتاج"
            },
            question: {
                en:
                    "Create a concise maintenance shift-handover note covering the symptom, machine state, alarms, actions taken, isolation state, unresolved risks, and next responsible person.",
                fr:
                    "Créez une note concise de passation de maintenance couvrant le symptôme, l'état de la machine, les alarmes, les actions réalisées, l'état d'isolement, les risques non résolus et le prochain responsable.",
                ar:
                    "أنشئ مذكرة مختصرة لتسليم أعمال الصيانة تشمل العَرَض وحالة الآلة والإنذارات والإجراءات المنفذة وحالة العزل والمخاطر غير المحسومة والمسؤول التالي."
            }
        }
    ];

    const modes = {
        troubleshooting: {
            en: "Troubleshooting",
            fr: "Recherche de panne",
            ar: "البحث عن الأعطال"
        },
        preventive_maintenance: {
            en: "Preventive maintenance",
            fr: "Maintenance préventive",
            ar: "الصيانة الوقائية"
        },
        safety_review: {
            en: "Safety review",
            fr: "Analyse de sécurité",
            ar: "مراجعة السلامة"
        },
        shift_handover: {
            en: "Shift handover",
            fr: "Passation de poste",
            ar: "تسليم المناوبة"
        },
        work_order: {
            en: "Work-order draft",
            fr: "Brouillon d'ordre de travail",
            ar: "مسودة أمر عمل"
        }
    };

    let timerHandle = null;
    let stageHandle = null;
    let startedAt = null;
    let stageIndex = 0;

    function currentLanguage() {
        return elements.language.value || "en";
    }

    function strings() {
        return translations[currentLanguage()] || translations.en;
    }

    function updateModeOptions() {
        const selectedMode = elements.taskMode.value;
        const language = currentLanguage();

        elements.taskMode.innerHTML = "";

        for (const [value, labels] of Object.entries(modes)) {
            const option = document.createElement("option");

            option.value = value;
            option.textContent = labels[language] || labels.en;

            if (value === selectedMode) {
                option.selected = true;
            }

            elements.taskMode.appendChild(option);
        }
    }

    function renderScenarios() {
        const language = currentLanguage();

        elements.scenarioList.innerHTML = "";

        for (const scenario of scenarios) {
            const button = document.createElement("button");

            button.type = "button";
            button.className = "scenario-card";
            button.dataset.scenarioId = scenario.id;

            const icon = document.createElement("span");
            icon.className = "scenario-icon";
            icon.textContent = scenario.icon;

            const copy = document.createElement("span");
            copy.className = "scenario-copy";

            const title = document.createElement("strong");
            title.textContent =
                scenario.title[language] ||
                scenario.title.en;

            const hint = document.createElement("small");
            hint.textContent =
                scenario.equipment[language] ||
                scenario.equipment.en;

            copy.append(title, hint);
            button.append(icon, copy);

            button.addEventListener("click", () => {
                applyScenario(scenario);
            });

            elements.scenarioList.appendChild(button);
        }
    }

    function applyScenario(scenario) {
        const language = currentLanguage();

        elements.machineName.value =
            scenario.equipment[language] ||
            scenario.equipment.en;

        elements.machineModel.value = "";

        elements.question.value =
            scenario.question[language] ||
            scenario.question.en;

        elements.question.dispatchEvent(
            new Event("input", {
                bubbles: true
            })
        );

        elements.question.focus();

        elements.chatForm.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }

    function buildStages() {
        const translation = strings();

        return elements.useDocuments.checked
            ? [
                translation.preparing,
                translation.searching,
                translation.generating,
                translation.structuring
            ]
            : [
                translation.preparing,
                translation.generating,
                translation.structuring
            ];
    }

    function renderStages(stages) {
        elements.progressStages.innerHTML = "";

        stages.forEach((stage, index) => {
            const item = document.createElement("li");

            item.textContent = stage;
            item.dataset.stageIndex = String(index);

            if (index === 0) {
                item.classList.add("is-active");
            }

            elements.progressStages.appendChild(item);
        });
    }

    function updateElapsedTime() {
        if (startedAt === null) {
            elements.progressTimer.textContent = "";
            return;
        }

        const elapsedSeconds = Math.floor(
            (Date.now() - startedAt) / 1000
        );

        elements.progressTimer.textContent =
            `${elapsedSeconds} ${strings().seconds}`;
    }

    function activateStage(index) {
        const items = Array.from(
            elements.progressStages.querySelectorAll("li")
        );

        items.forEach((item, itemIndex) => {
            item.classList.toggle(
                "is-active",
                itemIndex === index
            );

            item.classList.toggle(
                "is-complete",
                itemIndex < index
            );
        });

        const activeItem = items[index];

        if (activeItem) {
            elements.progressMessage.textContent =
                activeItem.textContent;
        }
    }

    function startProgress() {
        stopProgress(false);

        const translation = strings();
        const stages = buildStages();

        stageIndex = 0;
        startedAt = Date.now();

        elements.progressPanel.hidden = false;
        elements.progressTitle.textContent =
            translation.progressTitle;

        renderStages(stages);
        activateStage(0);
        updateElapsedTime();

        timerHandle = window.setInterval(
            updateElapsedTime,
            1000
        );

        stageHandle = window.setInterval(() => {
            if (stageIndex < stages.length - 1) {
                stageIndex += 1;
                activateStage(stageIndex);
            }
        }, 7000);
    }

    function stopProgress(hidePanel = true) {
        if (timerHandle !== null) {
            window.clearInterval(timerHandle);
            timerHandle = null;
        }

        if (stageHandle !== null) {
            window.clearInterval(stageHandle);
            stageHandle = null;
        }

        if (hidePanel) {
            elements.progressPanel.hidden = true;
        }

        startedAt = null;
        stageIndex = 0;
    }

    function normalizeAnswer(answer) {
        return String(answer || "")
            .toLocaleLowerCase()
            .replace(/\s+/g, " ");
    }

    function containsAny(answer, phrases) {
        return phrases.some((phrase) =>
            answer.includes(phrase)
        );
    }

    function classifySafety(answerText) {
        const answer = normalizeAnswer(answerText);
        const translation = strings();

        const stopWorkPhrases = [
            "keep the machine out of service",
            "must remain out of service",
            "stop work",
            "do not continue operation",
            "must not be operated",
            "condition d'arrêt",
            "maintenir la machine hors service",
            "ne pas poursuivre le fonctionnement",
            "إبقاء الآلة خارج الخدمة",
            "إيقاف العمل",
            "عدم مواصلة التشغيل"
        ];

        const escalationPhrases = [
            "qualified personnel",
            "authorized personnel",
            "escalate",
            "personnel qualifié",
            "personnel autorisé",
            "faire intervenir",
            "أشخاص مؤهلين",
            "أشخاص مصرح لهم",
            "التصعيد"
        ];

        const cautionPhrases = [
            "caution",
            "warning",
            "hazard",
            "danger",
            "uncertain",
            "insufficient information",
            "attention",
            "danger",
            "informations insuffisantes",
            "تحذير",
            "خطر",
            "المعلومات غير كافية"
        ];

        if (containsAny(answer, stopWorkPhrases)) {
            return {
                state: "stop",
                label: translation.safetyStop,
                text: translation.safetyStopText
            };
        }

        if (containsAny(answer, escalationPhrases)) {
            return {
                state: "escalate",
                label: translation.safetyEscalate,
                text: translation.safetyEscalateText
            };
        }

        if (containsAny(answer, cautionPhrases)) {
            return {
                state: "caution",
                label: translation.safetyCaution,
                text: translation.safetyCautionText
            };
        }

        return {
            state: "general",
            label: translation.safetyGeneral,
            text: translation.safetyGeneralText
        };
    }

    function updateSafetyState() {
        const answer = elements.answerText.textContent.trim();

        if (!answer) {
            elements.safetyState.hidden = true;
            return;
        }

        const result = classifySafety(answer);

        elements.safetyState.hidden = false;
        elements.safetyState.className =
            `safety-state safety-state-${result.state}`;

        elements.safetyStateLabel.textContent =
            result.label;

        elements.safetyStateText.textContent =
            result.text;
    }

    function requestAppearsComplete() {
        return (
            !elements.answerContent.hidden ||
            !elements.errorPanel.hidden
        );
    }

    elements.chatForm.addEventListener(
        "submit",
        () => {
            startProgress();
            elements.safetyState.hidden = true;
        }
    );

    const responseObserver = new MutationObserver(() => {
        if (!requestAppearsComplete()) {
            return;
        }

        stopProgress(true);

        if (!elements.answerContent.hidden) {
            updateSafetyState();
        }
    });

    responseObserver.observe(
        elements.answerContent,
        {
            attributes: true,
            attributeFilter: ["hidden"]
        }
    );

    responseObserver.observe(
        elements.errorPanel,
        {
            attributes: true,
            attributeFilter: ["hidden"]
        }
    );

    const answerObserver = new MutationObserver(() => {
        if (!elements.answerContent.hidden) {
            updateSafetyState();
        }
    });

    answerObserver.observe(
        elements.answerText,
        {
            childList: true,
            characterData: true,
            subtree: true
        }
    );

    elements.language.addEventListener(
        "change",
        () => {
            updateModeOptions();
            renderScenarios();

            if (!elements.safetyState.hidden) {
                updateSafetyState();
            }
        }
    );

    updateModeOptions();
    renderScenarios();

    console.info(
        "Siyana AI Sprint 1 enhancements loaded."
    );
})();
