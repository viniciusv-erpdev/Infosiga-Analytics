document.addEventListener("DOMContentLoaded", function () {

    const auditButtons = document.querySelectorAll(".btn-audit");

    const auditDate = document.getElementById("audit-date");
    const auditTime = document.getElementById("audit-time");
    const auditUser = document.getElementById("audit-user");

    auditButtons.forEach(button => {

        button.addEventListener("click", function () {

            const audit = this.dataset.audit || "";
            const user = this.dataset.user || "-";

            const parts = audit.split(" ");

            auditDate.textContent = parts[0] || "-";
            auditTime.textContent = parts[1] || "-";
            auditUser.textContent = user;

        });

    });

});