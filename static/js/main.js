document.addEventListener("DOMContentLoaded", function () {
    const emergencyButton = document.getElementById("testEmergencyButton");

    if (emergencyButton) {
        emergencyButton.addEventListener("click", async function () {
            const confirmed = confirm(
                "This is a test emergency.\n\nDo you want to simulate an SOS alert?"
            );

            if (!confirmed) {
                return;
            }

            emergencyButton.disabled = true;
            emergencyButton.textContent = "GETTING LOCATION...";

            try {
                const location = await getCurrentLocation();

                emergencyButton.textContent = "SENDING...";

                const response = await fetch("/api/emergency/", {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCookie("csrftoken"),
                    },

                    body: JSON.stringify({
                        trigger_type: "test",
                        latitude: location.latitude,
                        longitude: location.longitude,
                        message:
                            "Test emergency triggered from Guardian SHIELD dashboard.",
                    }),
                });

                const data = await response.json();

                if (response.ok) {
                    /*
                     * Parent Dashboard is now the main parent access link.
                     */
                    const parentDashboardUrl =
                        data.parent_dashboard_url;

                    if (parentDashboardUrl) {

                        showParentDashboardLink(
                            parentDashboardUrl,
                            data.incident_id
                        );

                        /*
                         * Try automatic clipboard copy.
                         */
                        let copied = false;

                        try {
                            if (
                                navigator.clipboard &&
                                window.isSecureContext
                            ) {
                                await navigator.clipboard.writeText(
                                    parentDashboardUrl
                                );

                                copied = true;
                            }
                        } catch (copyError) {
                            console.error(
                                "Automatic clipboard copy failed:",
                                copyError
                            );
                        }

                        /*
                         * Popup is only confirmation.
                         * Actual dashboard link remains visible
                         * on the webpage.
                         */
                        if (copied) {
                            alert(
                                "Emergency created successfully!\n\n" +
                                "Incident ID: #" +
                                data.incident_id +
                                "\n\n" +
                                "✅ Parent Dashboard Link is now available on the webpage.\n" +
                                "It was also copied to your clipboard."
                            );
                        } else {
                            alert(
                                "Emergency created successfully!\n\n" +
                                "Incident ID: #" +
                                data.incident_id +
                                "\n\n" +
                                "🔗 Parent Dashboard Link has been added to the webpage.\n\n" +
                                "Use the COPY LINK button there."
                            );
                        }

                    } else {
                        alert(
                            "Emergency created successfully!\n\n" +
                            "Incident ID: #" +
                            data.incident_id +
                            "\n\n" +
                            "Parent dashboard link was not returned."
                        );
                    }

                    /*
                     * DO NOT reload the page.
                     *
                     * The Parent Dashboard card must remain
                     * visible for testing.
                     */

                } else {
                    let errorMessage =
                        data.message ||
                        "Please check the entered data.";

                    if (data.errors) {
                        errorMessage +=
                            "\n\nDetails:\n" +
                            JSON.stringify(
                                data.errors,
                                null,
                                2
                            );
                    }

                    alert(
                        "Emergency could not be created.\n\n" +
                        errorMessage
                    );
                }

            } catch (error) {
                console.error(
                    "Emergency API error:",
                    error
                );

                alert(
                    "Unable to create emergency.\n\n" +
                    "Please allow location access and try again."
                );

            } finally {
                emergencyButton.disabled = false;
                emergencyButton.textContent =
                    "TEST EMERGENCY";
            }
        });
    }

    console.log(
        "Guardian SHIELD loaded successfully."
    );
});


/*
 * ---------------------------------------------------------
 * SHOW PARENT DASHBOARD LINK ON WEBPAGE
 * ---------------------------------------------------------
 */

function showParentDashboardLink(
    parentDashboardUrl,
    incidentId
) {
    /*
     * Remove an older card if it already exists.
     */
    const oldCard = document.getElementById(
        "parentDashboardLinkCard"
    );

    if (oldCard) {
        oldCard.remove();
    }

    /*
     * Create card.
     */
    const card = document.createElement("div");

    card.id = "parentDashboardLinkCard";

    card.style.margin = "25px 0";
    card.style.padding = "25px";
    card.style.borderRadius = "18px";
    card.style.background = "#ffffff";
    card.style.border = "2px solid #ef4444";
    card.style.boxShadow =
        "0 10px 30px rgba(0, 0, 0, 0.08)";

    /*
     * Card content.
     */
    card.innerHTML = `
        <div style="margin-bottom: 15px;">

            <div style="
                font-size: 13px;
                font-weight: 800;
                color: #dc2626;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                margin-bottom: 6px;
            ">
                🚨 Parent Live Tracking
            </div>

            <h2 style="
                margin: 0 0 8px;
                font-size: 22px;
                color: #111827;
            ">
                Parent Dashboard Link
            </h2>

            <p style="
                margin: 0;
                color: #6b7280;
                line-height: 1.5;
            ">
                Share this secure dashboard link with the parent.
                They can view emergency incidents and access
                live location tracking from one place.
            </p>

        </div>


        <div style="
            padding: 14px;
            background: #f3f4f6;
            border-radius: 12px;
            margin-bottom: 15px;
            word-break: break-all;
            font-family: monospace;
            font-size: 13px;
            line-height: 1.5;
            color: #111827;
        ">
            ${escapeHtml(parentDashboardUrl)}
        </div>


        <div style="
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        ">

            <button
                type="button"
                id="copyParentDashboardLink"
                style="
                    border: none;
                    padding: 13px 18px;
                    border-radius: 10px;
                    background: #111827;
                    color: #ffffff;
                    font-weight: 700;
                    cursor: pointer;
                "
            >
                📋 COPY LINK
            </button>


            <a
                href="${escapeAttribute(parentDashboardUrl)}"
                target="_blank"
                rel="noopener noreferrer"
                style="
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    padding: 13px 18px;
                    border-radius: 10px;
                    background: #dc2626;
                    color: #ffffff;
                    text-decoration: none;
                    font-weight: 700;
                "
            >
                🏠 OPEN PARENT DASHBOARD
            </a>

        </div>


        <div
            id="parentDashboardCopyStatus"
            style="
                margin-top: 12px;
                color: #16a34a;
                font-weight: 700;
                display: none;
            "
        ></div>


        <div style="
            margin-top: 12px;
            color: #9ca3af;
            font-size: 12px;
        ">
            Latest Incident #${incidentId}
        </div>
    `;


    /*
     * Insert card near the top of the dashboard.
     */
    const mainContent =
        document.querySelector("main") ||
        document.querySelector(
            ".dashboard-container"
        ) ||
        document.querySelector(
            ".container"
        ) ||
        document.body;

    mainContent.prepend(card);


    /*
     * Copy button.
     */
    const copyButton = document.getElementById(
        "copyParentDashboardLink"
    );

    const copyStatus = document.getElementById(
        "parentDashboardCopyStatus"
    );


    copyButton.addEventListener(
        "click",
        async function () {

            try {
                await copyTextToClipboard(
                    parentDashboardUrl
                );

                copyStatus.textContent =
                    "✅ Parent Dashboard Link copied successfully!";

                copyStatus.style.display =
                    "block";

                copyButton.textContent =
                    "✅ COPIED";

                setTimeout(function () {
                    copyButton.textContent =
                        "📋 COPY LINK";
                }, 2000);

            } catch (error) {

                console.error(
                    "Clipboard copy failed:",
                    error
                );


                /*
                 * Fallback copy method.
                 */
                const textArea =
                    document.createElement(
                        "textarea"
                    );

                textArea.value =
                    parentDashboardUrl;

                textArea.style.position =
                    "fixed";

                textArea.style.left =
                    "-9999px";

                document.body.appendChild(
                    textArea
                );

                textArea.focus();
                textArea.select();


                try {

                    document.execCommand(
                        "copy"
                    );

                    copyStatus.textContent =
                        "✅ Parent Dashboard Link copied successfully!";

                    copyStatus.style.display =
                        "block";

                    copyButton.textContent =
                        "✅ COPIED";

                } catch (fallbackError) {

                    console.error(
                        "Fallback copy failed:",
                        fallbackError
                    );

                    prompt(
                        "Copy the Parent Dashboard Link:",
                        parentDashboardUrl
                    );
                }


                document.body.removeChild(
                    textArea
                );
            }
        }
    );


    /*
     * Scroll directly to the dashboard link card.
     */
    card.scrollIntoView({
        behavior: "smooth",
        block: "center",
    });
}


/*
 * ---------------------------------------------------------
 * CLIPBOARD HELPER
 * ---------------------------------------------------------
 */

async function copyTextToClipboard(text) {

    if (
        navigator.clipboard &&
        window.isSecureContext
    ) {
        await navigator.clipboard.writeText(
            text
        );

        return;
    }

    throw new Error(
        "Modern clipboard API unavailable."
    );
}


/*
 * ---------------------------------------------------------
 * HTML ESCAPING
 * ---------------------------------------------------------
 */

function escapeHtml(text) {

    const div =
        document.createElement("div");

    div.textContent = text;

    return div.innerHTML;
}


function escapeAttribute(text) {

    return escapeHtml(text)
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}


/*
 * ---------------------------------------------------------
 * GET CURRENT GPS LOCATION
 * ---------------------------------------------------------
 */

function getCurrentLocation() {

    return new Promise(
        function (resolve, reject) {

            if (!navigator.geolocation) {

                reject(
                    new Error(
                        "Geolocation is not supported."
                    )
                );

                return;
            }


            navigator.geolocation.getCurrentPosition(

                function (position) {

                    resolve({
                        latitude:
                            position.coords.latitude,

                        longitude:
                            position.coords.longitude,
                    });
                },


                function (error) {

                    reject(error);
                },


                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0,
                }
            );
        }
    );
}


/*
 * ---------------------------------------------------------
 * CSRF COOKIE
 * ---------------------------------------------------------
 */

function getCookie(name) {

    const cookies =
        document.cookie.split(";");


    for (
        let cookie of cookies
    ) {

        cookie = cookie.trim();


        if (
            cookie.startsWith(
                name + "="
            )
        ) {

            return decodeURIComponent(
                cookie.substring(
                    name.length + 1
                )
            );
        }
    }


    return null;
}