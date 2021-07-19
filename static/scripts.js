// Global variables
var i = 1; // Count of active form selection fields vaccination
var l = 1; // Declaration of active form elements - vaccine select
var m = 1; // Declaration of active form elements - day select

// Execute function as soon as DOM is loaded
document.addEventListener('DOMContentLoaded', function() {

// Shows or hides vaccine selection (radio buttons) on register.html
    var registerRadios = document.querySelectorAll('#radio1, #radio2');
    var vaccineVisibility =  document.getElementById("vaccineVisibility");

    if (registerRadios != null) {
        for(var j = 0; j < registerRadios.length; j++) {
            // Radios deactivated by default - triggered if clicked
            registerRadios[j].onclick = function() {
               // Get value of radios and show / hide the respective html boxes
                var val = this.value;
                if(val == 'all'){
                    vaccineVisibility.style.display = 'none';    // hide
                }
                else if(val == 'select'){
                    vaccineVisibility.style.display = 'block';   // show
                }
             }
        }
    }

// Shows or hides Add Appointment section on index_office.html
    var addAppointment = document.getElementById("btn-addappointment");
    var boxAddAppointment =  document.getElementById("box-addAppointment");

    if (addAppointment != null) {
       addAppointment.onclick = function() {
            boxAddAppointment.style.display = 'block';    // show
            addAppointment.style.display = 'none';        // hide
        }
    }

// Duplicate form sections for vaccine selection
    var addVaccine =  document.getElementById("btn-addvaccine");
    if (addVaccine != null) {
        addVaccine.onclick = function() {
            // Create a clone of element
            let clone = document.querySelector("#vaccines_0").cloneNode(true);
            i += 1;
            l += 1;

            // Change the id attribute of the newly created element
            var id = "vaccines_" + l;
            clone.setAttribute('id', id);

            // Append the newly created element on ...
            document.querySelector('#vaccineSelect').appendChild(clone);

            // hide add button when all selected
            if (i > 2){
                addVaccine.style.display = 'none'; // hide
            }

            // Call function to remove child to set the events listener
            removeVaccine();
        }
    }

// Duplicate form sections for day selection on offer.html, offer_index.html
    var addDay =  document.getElementById("btn-addday");
    if (addDay != null) {
        addDay.onclick = function() {
            // Create a clone of element
            let clone = document.querySelector("#day_0").cloneNode(true);
            m += 1;

            // Change the id attribute of the newly created element
            var id = "day" + m;
            clone.setAttribute('id', id);

            // Append the newly created element on ...
            document.querySelector('#daySelect').appendChild(clone);

            // Call function to remove child to set the events listener
            removeDay();
        }
    }

// Index pages: Pages for showing or hiding html sections
    navIndex = document.querySelectorAll('.nav-index')
    if (navIndex != null) {
        document.getElementById("nav-index").addEventListener('click', function() {

            // First - Set focus in nav bar
            var navElements = document.querySelectorAll('.sub-nav-link')

            // Remove active class from all tabs - active: focuses a tab in html form
            navElements.forEach(function(item){
                item.classList.remove("active");
            });
            // Add active class to event trigger
            event.target.classList.add("active");

            // Second - Show or hide html sections
            var box = event.target.id;
            var indexBoxes = document.querySelectorAll('.indexBoxes');

            // Hide all sections
            indexBoxes.forEach(function(item){
                item.style.display = 'none';
            });

            // Show section of trigger element
            document.getElementById(box + "Box").style.display = 'block';
        });
    }
});

// Remove form sections - vaccine select
function removeVaccine() {
    var removeVaccine = document.querySelectorAll('.btn-removevaccine');

    for(var k = 0; k < removeVaccine.length; k++) {
        removeVaccine[k].onclick = function() {

            // Remove parent element of event trigger
            document.getElementById("vaccineSelect").removeChild(event.target.parentNode);

            // Adjust count of visible clones
            i -= 1;

            // Show Add Vaccine Button again if less than 3 Vaccines selected
            if (i < 3){
                document.getElementById("btn-addvaccine").style.display = 'block'; // show
            }

        }
    }
};

// Remove form sections - day select
function removeDay() {
    var removeDay = document.querySelectorAll('.btn-removeday');

    for(var k = 0; k < removeDay.length; k++) {
        removeDay[k].onclick = function() {
            // Remove parent element of event trigger
            document.getElementById("daySelect").removeChild(event.target.parentNode);
        }
    }
};