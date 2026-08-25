document.addEventListener("DOMContentLoaded", () => {

    const elements = document.querySelectorAll(
        ".text-capitalize-frontend"
    );

    elements.forEach(element => {

        const text = element.textContent.trim();

        if (!text) {
            return;
        }

        element.textContent = text
            .toLocaleLowerCase("pt-BR")
            .split(/\s+/)
            .map(word => {

                if (!word) {
                    return "";
                }

                return (
                    word.charAt(0).toLocaleUpperCase("pt-BR") +
                    word.slice(1)
                );

            })
            .join(" ");

    });

});