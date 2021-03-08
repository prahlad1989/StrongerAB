function round2Decimals( decimals){
    var displayToDecimals =function (value,item){
         if(!value){
        return value;
     }
    else{
        tensPower = Math.pow(10,decimals);
        return Math.round(value*tensPower)/tensPower;
        }
    }
   return displayToDecimals;
}

