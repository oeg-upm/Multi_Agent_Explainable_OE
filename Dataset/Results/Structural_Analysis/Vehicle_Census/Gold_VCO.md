``````mermaid
classDiagram

    Owner --> unionOwner : subClassOf
    unionOwner ..> Person
    unionOwner ..> Organization
 class unionOwner["(Organization ⊔ Person)"]
   
    class Tramo {
    
    }

    class Owner {
    
    }

    class Permit {
    
    }

    class Vehicle {
    
    }

    class Person {
    
    }

    class RegulatedZone {
    
    }


    class Organization {
    
    }

   
    
    

Permit  --> Owner   :permitOwner  

Vehicle  --> Owner   :registeredOwner  

Permit  --> Vehicle   :authorisesVehicle  

Permit  --> Tramo   :authorisesInSegment  

    
    class Permit  {
    
    
        endingDate  
     
        beginningDate  
     
        activationDate  
     
    } 
    
    class Vehicle  {
    
    
        licensePlateNumber  
     
    }
```

```

```
``````
