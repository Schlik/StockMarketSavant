
function drag(ev)
{
   console.log("drag()");
   ev.dataTransfer.clearData();
   ev.dataTransfer.setData("text", ev.target.id);
   ev.dataTransfer.setDragImage(ev.target,0,0);
   ev.dataTransfer.effectAllowed='move';
   return true;
}

function allowDrop(ev) 
{
   console.log("allowDrop()");
   ev.preventDefault();
   return true;
}


function drop(ev) 
{
   console.log("drop()");

   ev.preventDefault();

   var data = ev.dataTransfer.getData("text");

   if(  document.getElementById(data).parentElement.getAttribute("group") !=  
                                            ev.target.parentElement.getAttribute("valid_drop_group"))
   {
      console.log( "not equal grooups");
      return
   }

   //set value of alt for this node
   ev.target.alt = document.getElementById(data).alt;

   //set the image so that this node now matches the one being dropped
   ev.target.src = document.getElementById(data).src;

   //set the return value in the form when submit is clicked
   var result_id = ev.target.parentElement.id.replace("-winner","");
   console.log( result_id ); 
   document.getElementById( result_id ).setAttribute("value", document.getElementById(data).alt);
}
