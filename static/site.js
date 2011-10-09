function addTerms(arrterms){
    for (term in arrterms){
	// Doing it this way because jquery append has been causing funky behaviors
	$("#terms").val($("#terms").val() + arrterms[term] + "\r\n");
    }
}

function clearTerms(){
    $("#terms").val("");
}