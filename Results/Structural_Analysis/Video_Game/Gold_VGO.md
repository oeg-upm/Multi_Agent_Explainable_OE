`

```mermaid
classDiagram

    
    class PopulatedPlace {
    
    }

    class ProductOrService {
    
    }

    class Achievement {
    
    }

    class Character {
    
    }

    class Collection {
    
    }

    class Completion {
    
    }

    class Curiosity {
    
    }

    class Fandom {
    
    }

    class Feature {
    
    }

    class GainEvent {
    
    }

    class Game {
    
    }

    class GameEvent {
    
    }

    class GameProduct {
    
    }

    class Genre {
    
    }

    class HardMode {
    
    }

    class InAppPurchaseEvent {
    
    }

    class InstantaneousEvent {
    
    }

    class Item {
    
    }

    class Leaderboard {
    
    }

    class LoseEvent {
    
    }

    class Loyalty {
    
    }

    class Luck {
    
    }

    class MenuEvent {
    
    }

    class Minigame {
    
    }

    class Multiplayer {
    
    }

    class Paragon {
    
    }

    class Player {
    
    }

    class PlayerEvent {
    
    }

    class PlayingArea {
    
    }

    class Session {
    
    }

    class SpecialPlayStyle {
    
    }

    class Tutorial {
    
    }

    class Veteran {
    
    }

    class Virtuosity {
    
    }

    class Product {
    
    }

    class Thing {
    
    }

    class Agent {
    
    }


    
    Achievement <|-- Collection 
    
    Achievement <|-- Completion 
    
    Achievement <|-- Curiosity 
    
    Achievement <|-- Fandom 
    
    Achievement <|-- HardMode 
    
    Achievement <|-- Loyalty 
    
    Achievement <|-- Luck 
    
    Achievement <|-- Minigame 
    
    Achievement <|-- Multiplayer 
    
    Achievement <|-- Paragon 
    
    Achievement <|-- SpecialPlayStyle 
    
    Achievement <|-- Tutorial 
    
    Achievement <|-- Veteran 
    
    Achievement <|-- Virtuosity 
    
    GameEvent <|-- GainEvent 
    
    GameEvent <|-- LoseEvent 
    
    InstantaneousEvent <|-- GameEvent 
    
    InstantaneousEvent <|-- InAppPurchaseEvent 
    
    InstantaneousEvent <|-- MenuEvent 
    
    InstantaneousEvent <|-- PlayerEvent 
    
    Product <|-- GameProduct 
    
    Thing <|-- Leaderboard 
    
    Thing <|-- Session 
    
    Agent <|-- Player 
    

Game  --> Agent   :creator  

Game  --> Achievement   :hasAchievement  

Game  --> Character   :hasCharacter  

Item  --> Feature   :hasFeature  

Game  --> Genre   :hasGameGenre  

Game  --> Item   :hasItem  

Game  --> Leaderboard   :hasLeaderboard  

Game  --> PlayingArea   :hasPlayingArea  

Session  --> Achievement   :involvesAchievement  

Session  --> Character   :involvesCharacter  

Session  --> Player   :involvesPlayer  

Achievement  --> Session   :isAchievedInSession  

Achievement  --> Game   :isAchievementInGame  

Character  --> Game   :isCharacterInGame  

Character  --> Session   :isCharacterInSession  

InstantaneousEvent  --> Player   :isEventAssociatedToPlayer  

InstantaneousEvent  --> Game   :isEventInGame  

InstantaneousEvent  --> Session   :isEventInSession  

InstantaneousEvent  --> Item   :isEventRelatedToItem  

InstantaneousEvent  --> Character   :isEventTriggeredByCharacter  

Player  --> Player   :isFriendWithPlayer  

Item  --> Game   :isItemInGame  

Leaderboard  --> Game   :isLeaderboardInGame  

Player  --> Session   :isPlayerInSession  

Session  --> Game   :isSessionInGame  

Player  --> PopulatedPlace   :livesIn  

Player  --> Achievement   :ownsAchievement  

Player  --> Character   :ownsCharacter  

Character  --> Item   :ownsItem  

Player  --> Game   :playsGame  

InAppPurchaseEvent  --> GameProduct   :purchasesGameOffering  

InstantaneousEvent  --> Achievement   :unlocksAchievement  

    
    class Session  {
    
    
        endTime  
     
        startTime  
     
    } 
    
    class InstantaneousEvent  {
    
    
        eventName  
     
        eventTime  
     
    } 
    
    class Game  {
    
    
        releaseDate  
     
    } 
    
    class Player  {
    
    
        username  
     
    }
`
```

```

```
