"use strict";

/*
 * Siyana AI — Sprint 2 local knowledge experience
 *
 * Adds:
 * - Direct manual search
 * - Search-result rendering
 * - "Use in question" action
 * - Expandable excerpts
 * - Copy excerpt action
 * - Improved citation interactions
 *
 * Existing backend contracts remain unchanged.
 */

(() => {
    const byId = (id) => document.getElementById(id);

    const elements = {
        language: byId("language"),
        question: byId("question"),
        additionalContext: byId("additionalContext"),

        manualSearchForm: byId("manualSearchForm"),
        manualSearchInput: byId("manualSearchInput"),
        manualSearchLimit: byId("manualSearchLimit"),
        manualSearchButton: byId("manualSearchButton"),
        manualSearchButtonText:
            byId("manualSearchButtonText"),

        manualSearchMessage:
            byId("manualSearchMessage"),

        manualSearchResults:
            byId("manualSearchResults"),

        manualSearchEmpty:
            byId("manualSearchEmpty"),

        manualSearchCount:
            byId("manualSearchCount"),

        citationsSection:
            byId("citationsSection"),

        citationList:
            byId("citationList")
    };

    const requiredElements = [
        "language",
        "question",
        "additionalContext",
        "manualSearchForm",
        "manualSearchInput",
        "manualSearchLimit",
        "manualSearchButton",
        "manualSearchButtonText",
        "manualSearchMessage",
        "manualSearchResults",
        "manualSearchEmpty",
        "manualSearchCount",
        "citationsSection",
        "citationList"
    ];

    const missingElements = requiredElements.filter(
        (name) => !elements[name]
    );

    if (missingElements.length > 0) {
        console.error(
            "Sprint 2 could not start. Missing elements:",
            missingElements
        );

        return;
    }

    const translations = {
        en: {
            searchButton: "Search manuals",
            searching: "Searching locally…",
            emptyTitle: "Search the local knowledge base",
            emptyText:
                "Enter an equipment term, symptom, component, or alarm code.",
            noResultsTitle: "No relevant passage found",
            noResultsText:
                "Try a shorter query, another technical term, or import a relevant manual.",
            resultSingle: "result",
            resultPlural: "results",
            page: "Page",
            relevance: "Relevance",
            useInQuestion: "Use in question",
            addedToQuestion: "Added to question",
            copyExcerpt: "Copy excerpt",
            copied: "Copied",
            expand: "Show full excerpt",
            collapse: "Show less",
            localResult: "LOCAL RESULT",
            searchError:
                "The local manual search could not be completed.",
            minimumQuery:
                "Enter at least two characters to search.",
            sourceReference: "Local manual reference",
            sourceInstruction:
                "Use the following local manual passage as supporting context. Verify all actions against the original document.",
            directSearchNote:
                "Searches run locally through the indexed manual library."
        },

        fr: {
            searchButton: "Rechercher dans les manuels",
            searching: "Recherche locale…",
            emptyTitle: "Rechercher dans la base locale",
            emptyText:
                "Saisissez un équipement, un symptôme, un composant ou un code d'alarme.",
            noResultsTitle: "Aucun passage pertinent trouvé",
            noResultsText:
                "Essayez une requête plus courte, un autre terme technique ou importez un manuel adapté.",
            resultSingle: "résultat",
            resultPlural: "résultats",
            page: "Page",
            relevance: "Pertinence",
            useInQuestion: "Utiliser dans la question",
            addedToQuestion: "Ajouté à la question",
            copyExcerpt: "Copier l'extrait",
            copied: "Copié",
            expand: "Afficher tout l'extrait",
            collapse: "Réduire",
            localResult: "RÉSULTAT LOCAL",
            searchError:
                "La recherche dans les manuels locaux n'a pas pu être effectuée.",
            minimumQuery:
                "Saisissez au moins deux caractères.",
            sourceReference: "Référence du manuel local",
            sourceInstruction:
                "Utilisez le passage suivant comme contexte. Vérifiez toute intervention dans le document d'origine.",
            directSearchNote:
                "La recherche est effectuée localement dans les manuels indexés."
        },

        ar: {
            searchButton: "البحث في الأدلة",
            searching: "جارٍ البحث محلياً…",
            emptyTitle: "البحث في قاعدة المعرفة المحلية",
            emptyText:
                "أدخل اسم معدة أو عَرَضاً أو مكوناً أو رمز إنذار.",
            noResultsTitle: "لم يتم العثور على مقطع مناسب",
            noResultsText:
                "جرب عبارة أقصر أو مصطلحاً فنياً آخر أو استورد دليلاً مناسباً.",
            resultSingle: "نتيجة",
            resultPlural: "نتائج",
            page: "الصفحة",
            relevance: "الصلة",
            useInQuestion: "استخدامه في السؤال",
            addedToQuestion: "تمت إضافته إلى السؤال",
            copyExcerpt: "نسخ المقطع",
            copied: "تم النسخ",
            expand: "عرض المقطع كاملاً",
            collapse: "عرض أقل",
            localResult: "نتيجة محلية",
            searchError:
                "تعذر إكمال البحث في الأدلة المحلية.",
            minimumQuery:
                "أدخل حرفين على الأقل للبحث.",
            sourceReference: "مرجع الدليل المحلي",
            sourceInstruction:
                "استخدم المقطع التالي كسياق داعم، وتحقق من جميع الإجراءات في المستند الأصلي.",
            directSearchNote:
                "يتم البحث محلياً في مكتبة الأدلة المفهرسة."
        }
    };

    let latestResults = [];

    function currentLanguage() {
        return elements.language.value || "en";
    }

    function strings() {
        return (
            translations[currentLanguage()] ||
            translations.en
        );
    }

    function setSearchLoading(loading) {
        elements.manualSearchButton.disabled =
            loading;

        elements.manualSearchButtonText.textContent =
            loading
                ? strings().searching
                : strings().searchButton;

        elements.manualSearchForm.classList.toggle(
            "is-searching",
            loading
        );
    }

    function showSearchMessage(
        message,
        state = "information"
    ) {
        elements.manualSearchMessage.hidden = false;

        elements.manualSearchMessage.className =
            `manual-search-message manual-search-message-${state}`;

        elements.manualSearchMessage.textContent =
            message;
    }

    function hideSearchMessage() {
        elements.manualSearchMessage.hidden = true;
        elements.manualSearchMessage.textContent = "";
    }

    function relevanceLabel(rank, index) {
        /*
         * SQLite FTS5 BM25 values are normally lower for
         * better results and may be negative. We avoid
         * presenting a fake numerical percentage.
         */

        if (index === 0) {
            return "Best match";
        }

        if (index <= 2) {
            return "Strong match";
        }

        return "Related";
    }

    function createEmptyState(
        title,
        message,
        state = "empty"
    ) {
        elements.manualSearchResults.innerHTML = "";

        const container = document.createElement("div");

        container.className =
            `manual-search-state manual-search-state-${state}`;

        const symbol = document.createElement("span");
        symbol.className = "manual-search-state-symbol";
        symbol.textContent =
            state === "no-results" ? "?" : "⌕";

        const copy = document.createElement("div");

        const heading = document.createElement("strong");
        heading.textContent = title;

        const paragraph = document.createElement("p");
        paragraph.textContent = message;

        copy.append(heading, paragraph);
        container.append(symbol, copy);

        elements.manualSearchResults.appendChild(
            container
        );

        elements.manualSearchCount.textContent = "";
    }

    function createResultCard(result, index) {
        const translation = strings();

        const article = document.createElement("article");
        article.className = "manual-result-card";

        const header = document.createElement("div");
        header.className = "manual-result-header";

        const sourceBlock = document.createElement("div");

        const label = document.createElement("span");
        label.className = "manual-result-label";

        label.textContent =
            `${translation.localResult} ${index + 1}`;

        const title = document.createElement("strong");
        title.className = "manual-result-title";
        title.textContent = result.filename;

        sourceBlock.append(label, title);

        const pageBadge = document.createElement("span");
        pageBadge.className = "manual-result-page";

        pageBadge.textContent =
            `${translation.page} ${result.page_number}`;

        header.append(sourceBlock, pageBadge);

        const relevance = document.createElement("div");
        relevance.className = "manual-result-relevance";

        const relevanceDot = document.createElement("span");
        relevanceDot.setAttribute("aria-hidden", "true");

        const relevanceText =
            document.createElement("span");

        relevanceText.textContent =
            `${translation.relevance}: ` +
            relevanceLabel(result.rank, index);

        relevance.append(
            relevanceDot,
            relevanceText
        );

        const excerptWrapper =
            document.createElement("div");

        excerptWrapper.className =
            "manual-result-excerpt-wrapper";

        const excerpt = document.createElement("p");
        excerpt.className = "manual-result-excerpt";
        excerpt.textContent = result.content;

        const isLong =
            String(result.content || "").length > 520;

        if (isLong) {
            excerpt.classList.add("is-collapsed");
        }

        excerptWrapper.appendChild(excerpt);

        const actions = document.createElement("div");
        actions.className = "manual-result-actions";

        const useButton = document.createElement("button");
        useButton.type = "button";
        useButton.className =
            "manual-result-action manual-result-action-primary";

        useButton.textContent =
            translation.useInQuestion;

        useButton.addEventListener("click", () => {
            addResultToQuestion(
                result,
                useButton
            );
        });

        const copyButton = document.createElement("button");
        copyButton.type = "button";
        copyButton.className = "manual-result-action";
        copyButton.textContent =
            translation.copyExcerpt;

        copyButton.addEventListener(
            "click",
            async () => {
                try {
                    await navigator.clipboard.writeText(
                        result.content
                    );

                    copyButton.textContent =
                        translation.copied;

                    window.setTimeout(() => {
                        copyButton.textContent =
                            strings().copyExcerpt;
                    }, 1400);

                } catch (error) {
                    console.error(
                        "Unable to copy manual excerpt:",
                        error
                    );
                }
            }
        );

        actions.append(useButton, copyButton);

        if (isLong) {
            const expandButton =
                document.createElement("button");

            expandButton.type = "button";
            expandButton.className =
                "manual-result-action";

            expandButton.textContent =
                translation.expand;

            expandButton.addEventListener(
                "click",
                () => {
                    const collapsed =
                        excerpt.classList.toggle(
                            "is-collapsed"
                        );

                    expandButton.textContent =
                        collapsed
                            ? strings().expand
                            : strings().collapse;
                }
            );

            actions.appendChild(expandButton);
        }

        article.append(
            header,
            relevance,
            excerptWrapper,
            actions
        );

        return article;
    }

    function renderResults(results) {
        latestResults = results;

        const translation = strings();

        if (!results.length) {
            createEmptyState(
                translation.noResultsTitle,
                translation.noResultsText,
                "no-results"
            );

            return;
        }

        elements.manualSearchResults.innerHTML = "";

        const countLabel =
            results.length === 1
                ? translation.resultSingle
                : translation.resultPlural;

        elements.manualSearchCount.textContent =
            `${results.length} ${countLabel}`;

        results.forEach((result, index) => {
            elements.manualSearchResults.appendChild(
                createResultCard(result, index)
            );
        });
    }

    function buildSourceReference(result) {
        const translation = strings();

        return [
            "",
            `${translation.sourceReference}:`,
            `${result.filename}, ` +
                `${translation.page} ${result.page_number}`,
            "",
            translation.sourceInstruction,
            "",
            result.content
        ].join("\n");
    }

    function addResultToQuestion(result, button) {
        const reference = buildSourceReference(result);

        const currentContext =
            elements.additionalContext.value.trim();

        elements.additionalContext.value =
            currentContext
                ? `${currentContext}\n\n${reference.trim()}`
                : reference.trim();

        elements.additionalContext.dispatchEvent(
            new Event("input", {
                bubbles: true
            })
        );

        button.textContent =
            strings().addedToQuestion;

        button.disabled = true;

        elements.question.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });

        elements.question.focus();

        window.setTimeout(() => {
            button.disabled = false;
            button.textContent =
                strings().useInQuestion;
        }, 1800);
    }

    async function searchManuals(event) {
        event.preventDefault();

        const query =
            elements.manualSearchInput.value.trim();

        if (query.length < 2) {
            showSearchMessage(
                strings().minimumQuery,
                "warning"
            );

            elements.manualSearchInput.focus();
            return;
        }

        hideSearchMessage();
        setSearchLoading(true);

        const limit = Number(
            elements.manualSearchLimit.value
        );

        const parameters = new URLSearchParams({
            q: query,
            limit: String(limit)
        });

        try {
            const response = await fetch(
                `/api/documents/search?${parameters.toString()}`,
                {
                    method: "GET",
                    headers: {
                        "Accept": "application/json"
                    },
                    cache: "no-store"
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
                    data &&
                    typeof data.detail === "string"
                        ? data.detail
                        : strings().searchError;

                throw new Error(message);
            }

            const results =
                data &&
                Array.isArray(data.results)
                    ? data.results
                    : [];

            renderResults(results);

        } catch (error) {
            console.error(
                "Local manual search failed:",
                error
            );

            showSearchMessage(
                error instanceof Error
                    ? error.message
                    : strings().searchError,
                "error"
            );

            createEmptyState(
                strings().noResultsTitle,
                strings().searchError,
                "error"
            );

        } finally {
            setSearchLoading(false);
        }
    }

    function enhanceCitationCards() {
        const citationCards =
            elements.citationList.querySelectorAll(
                ".citation-card, .citation-item"
            );

        citationCards.forEach((card, index) => {
            if (
                card.querySelector(
                    ".sprint2-citation-actions"
                )
            ) {
                return;
            }

            const paragraph =
                card.querySelector("p");

            if (!paragraph) {
                return;
            }

            card.classList.add(
                "sprint2-enhanced-citation"
            );

            const actions =
                document.createElement("div");

            actions.className =
                "sprint2-citation-actions";

            const copyButton =
                document.createElement("button");

            copyButton.type = "button";
            copyButton.textContent =
                strings().copyExcerpt;

            copyButton.addEventListener(
                "click",
                async () => {
                    try {
                        await navigator.clipboard.writeText(
                            paragraph.textContent || ""
                        );

                        copyButton.textContent =
                            strings().copied;

                        window.setTimeout(() => {
                            copyButton.textContent =
                                strings().copyExcerpt;
                        }, 1400);

                    } catch (error) {
                        console.error(
                            "Unable to copy citation:",
                            error
                        );
                    }
                }
            );

            const contentLength =
                paragraph.textContent.length;

            if (contentLength > 360) {
                paragraph.classList.add(
                    "is-collapsed"
                );

                const expandButton =
                    document.createElement("button");

                expandButton.type = "button";
                expandButton.textContent =
                    strings().expand;

                expandButton.addEventListener(
                    "click",
                    () => {
                        const collapsed =
                            paragraph.classList.toggle(
                                "is-collapsed"
                            );

                        expandButton.textContent =
                            collapsed
                                ? strings().expand
                                : strings().collapse;
                    }
                );

                actions.appendChild(expandButton);
            }

            actions.appendChild(copyButton);
            card.appendChild(actions);
        });

        elements.citationsSection.classList.add(
            "sprint2-citations"
        );
    }

    const citationObserver = new MutationObserver(
        () => {
            enhanceCitationCards();
        }
    );

    citationObserver.observe(
        elements.citationList,
        {
            childList: true,
            subtree: true
        }
    );

    elements.manualSearchForm.addEventListener(
        "submit",
        searchManuals
    );

    elements.language.addEventListener(
        "change",
        () => {
            elements.manualSearchButtonText.textContent =
                strings().searchButton;

            if (latestResults.length > 0) {
                renderResults(latestResults);
            }

            enhanceCitationCards();
        }
    );

    createEmptyState(
        strings().emptyTitle,
        strings().emptyText,
        "empty"
    );

    enhanceCitationCards();

    console.info(
        "Siyana AI Sprint 2 enhancements loaded."
    );
})();
