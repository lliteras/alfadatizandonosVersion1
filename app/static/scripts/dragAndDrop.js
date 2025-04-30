const loading = (e) => {
    if ($("#file-upload")[0].files.length == 0) {
        alert("Suba un archivo!")
        e.preventDefault()
        return
    }
    const parts = $("#file-upload")[0].files[0].name.split(".")
    if (!["csv", "CSV", "json", "JSON"].includes(parts[parts.length - 1])) {
        alert("Extensión no soportada")
        e.preventDefault()
        return
    }
    const delayInMilliseconds = 100
    setTimeout(function() {
        $("#file-upload-form").addClass("d-none")
        $("#carga").removeClass("d-none")     
    }, delayInMilliseconds);
}

$("#submit-button").on("click", loading)