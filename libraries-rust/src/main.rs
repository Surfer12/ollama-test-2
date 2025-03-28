use anymap::AnyMap;
use enum_dispatch::enum_dispatch;
use serde::{Deserialize, Serialize};
use serde_json;
use strum::IntoEnumIterator;
use strum_macros::EnumIter;
use thiserror::Error;
use typestate::typestate;

#[derive(Serialize, Deserialize, Debug)]
struct Point {
    x: i32,
    y: i32,
}

#[typestate]
enum State {
    Initial,
    Intermediate,
    Final,
}

#[enum_dispatch]
trait Shape {
    fn area(&self) -> f64;
}

struct Circle {
    radius: f64,
}

impl Shape for Circle {
    fn area(&self) -> f64 {
        std::f64::consts::PI * self.radius * self.radius
    }
}

struct Square {
    side: f64,
}

impl Shape for Square {
    fn area(&self) -> f64 {
        self.side * self.side
    }
}

#[derive(EnumIter, IntoEnumIterator)]
enum Color {
    Red,
    Green,
    Blue,
}

#[derive(Error, Debug)]
enum MyError {
    #[error("an addition error occurred")]
    AdditionError,
    #[error("a subtraction error occurred")]
    SubtractionError,
}

fn main() {
    let point = Point { x: 10, y: 20 };
    let serialized = serde_json::to_string(&point).unwrap();
    println!("Serialized: {}", serialized);

    let deserialized: Point = serde_json::from_str(&serialized).unwrap();
    println!("Deserialized: {:?}", deserialized);

    let initial = State::Initial;
    let intermediate = initial.transition();
    let final_state = intermediate.transition();

    let shapes: Vec<Box<dyn Shape>> = vec![
        Box::new(Circle { radius: 5.0 }),
        Box::new(Square { side: 4.0 }),
    ];

    for shape in shapes {
        println!("Area: {}", shape.area());
    }

    for color in Color::iter() {
        println!("{:?}", color);
    }

    let mut map = AnyMap::new();
    map.insert(42);
    map.insert("value");

    let value1: i32 = *map.get::<i32>().unwrap();
    let value2: &str = map.get::<&str>().unwrap();

    println!("value1: {}", value1);
    println!("value2: {}", value2);

    let result: Result<(), MyError> = Err(MyError::AdditionError);
    println!("Error: {:?}", result);
}
