````mermaid
classDiagram

    
    class Vehicle {
    
    }

    class Person {
    
    }

    class Organization {
    
    }

    class Owner {
    
    }

    class Authorization {
    
    }

    class RegulatedZone {
    
    }

    class ParkingZone {
    
    }

    class LowEmissionZone {
    
    }

    class EconomicInterestZone {
    
    }

    class HistoricalCaseZone {
    
    }

    class RoadSegment {
    
    }

    class Road {
    
    }

    class EnvironmentalBadge {
    
    }

    class AuthorizationType {
    
    }

    class VehicleType {
    
    }


    
    RegulatedZone <|-- ParkingZone 
    
    RegulatedZone <|-- LowEmissionZone 
    
    RegulatedZone <|-- EconomicInterestZone 
    
    RegulatedZone <|-- HistoricalCaseZone 
    

Vehicle  --> Owner   :hasVehicleOwner  

Authorization  --> Owner   :hasAuthorizationOwner  

Authorization  --> Vehicle   :authorizes  

Authorization  --> RoadSegment   :validOn  

Authorization  --> RegulatedZone   :authorizesIn  

RoadSegment  --> Road   :belongsTo  

Vehicle  --> EnvironmentalBadge   :hasEnvironmentalBadge  

Authorization  --> AuthorizationType   :hasAuthorizationType  

Vehicle  --> VehicleType   :hasVehicleType  

Owner  --> Vehicle   :ownerOfVehicle  

Owner  --> Authorization   :ownerOfAuthorization  

Vehicle  --> Authorization   :isAuthorizedBy  

RoadSegment  --> Authorization   :isValidFor  

RegulatedZone  --> Authorization   :zoneOfAuthorization  

Road  --> RoadSegment   :hasSegment  

EnvironmentalBadge  --> Vehicle   :isBadgeOf  

AuthorizationType  --> Authorization   :isTypeOfAuthorization  

VehicleType  --> Vehicle   :isTypeOfVehicle  

    
    class Authorization  {
    
    
        hasState  
     
        hasPeriodicity  
     
    }
`

```

```
````
