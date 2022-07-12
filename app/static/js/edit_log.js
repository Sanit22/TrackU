const datetime = document.getElementById("datetime");
const form = document.getElementById("log_form");
const timestamp = document.getElementById("timestamp");

form.onsubmit = function(){
    timestamp.value = datetime.value;
}
