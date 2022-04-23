const subir = () => {
    $("#file-upload-form").addClass("d-none")
    $("#carga").removeClass("d-none")
    data.append("file", $("#file-upload")[0].files[0])
    $.ajax({
        url: window.uploadUrl,
        data: data,
        cache: false,
        contentType: false,
        processData: false,
        method: 'POST',
        type: 'POST',
      })
        .done(function( data ) {
          if ( console && console.log ) {
            console.log( "Sample of data:", data );
          }
        });
}