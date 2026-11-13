
document.addEventListener("DOMContentLoaded", () => {

    const modal = document.getElementById("newAssessmentModal");
    const form = document.getElementById("newAssessmentForm");

    const targetSelect = document.getElementById("targetSelect");
    const tcpCheckbox = document.getElementById("tcpConnectivity");
    const portsSection = document.getElementById("portsSection");
    const portsInput = document.getElementById("portsInput");

    const errorMessage = document.getElementById("assessmentError");
    const createButton = document.getElementById("createAssessmentBtn");

    // Load targets whenever the modal opens.
    modal.addEventListener("show.bs.modal", loadTargets);

    async function loadTargets() {

        targetSelect.innerHTML = '<option value="">Loading targets...</option>';
        targetSelect.disabled = true;

        try {
            const response = await fetch(form.dataset.targetsUrl);

            if (!response.ok) {
                throw new Error("Unable to retrieve targets.");
            }

            const targets = await response.json();

            targetSelect.innerHTML = '<option value="">Select a target</option>';

            targets.forEach(target => {
                const option = document.createElement("option");

                option.value = target.target_id;
                option.textContent =
                    `${target.name} (${target.ip_address})`;

                targetSelect.appendChild(option);
            });

            if (targets.length === 0) {
                targetSelect.innerHTML =
                    '<option value="">No enabled targets available</option>';
            }

            targetSelect.disabled = targets.length === 0;

        } catch (error) {
            targetSelect.innerHTML =
                '<option value="">Failed to load targets</option>';

            showError(error.message);
        }
    }

    // Show the port input only when TCP Connectivity is selected.
    tcpCheckbox.addEventListener("change", () => {

        if (tcpCheckbox.checked) {
            portsSection.classList.remove("d-none");
            portsInput.required = true;
        } else {
            portsSection.classList.add("d-none");
            portsInput.required = false;
            portsInput.value = "";
        }
    });

    // Submit a new assessment.
    form.addEventListener("submit", async (event) => {

        event.preventDefault();
        hideError();

        const targetId = targetSelect.value;

        const selectedTests = Array.from(
            form.querySelectorAll('input[name="test_type"]:checked')
        ).map(input => input.value);

        // Basic validation.
        if (!targetId) {
            showError("Please select a target.");
            return;
        }

        if (selectedTests.length === 0) {
            showError("Please select at least one assessment test.");
            return;
        }

        // Parse the port input.
        let ports = [];

        if (tcpCheckbox.checked) {

            ports = portsInput.value
                .split(",")
                .map(port => port.trim())
                .map(port => Number(port));

            if (
                ports.length === 0 ||
                ports.some(port =>
                    !Number.isInteger(port) ||
                    port < 1 ||
                    port > 65535
                )
            ) {
                showError("Please enter valid TCP ports between 1 and 65535.");
                return;
            }

            if (new Set(ports).size !== ports.length) {
                showError("Duplicate ports are not allowed.");
                return;
            }
        }

        const assessmentData = {
            target_id: Number(targetId),
            test_type: selectedTests,
            ports: ports
        };

        try {

            createButton.disabled = true;
            createButton.textContent = "Creating...";

            const response = await fetch(form.dataset.createUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(assessmentData)
            });

            const result = await response.json().catch(() => null);

            if (!response.ok) {
                throw new Error(
                    result?.error || "Failed to create assessment."
                );
            }

            // Close modal and refresh the assessments page.
            bootstrap.Modal.getInstance(modal).hide();

            window.location.reload();

        } catch (error) {
            showError(error.message);

        } finally {
            createButton.disabled = false;
            createButton.innerHTML =
                '<i class="bi bi-plus-lg me-1"></i> Create Assessment';
        }
    });

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove("d-none");
    }

    function hideError() {
        errorMessage.textContent = "";
        errorMessage.classList.add("d-none");
    }

});
