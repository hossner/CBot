#include <Wire.h>

#define SLAVE_ADDRESS 0x04
#define DELAY_LOOP 20

int retVal = 0;
int cmdVal = 0;

// For CMD_TOGGLE_LED = 1
#define PIN_LED 13
int LEDstate = 0;

// For CMD_READ_TEMP = 2
double temp;

// For CMD_GET_DIST_1 = 3
// MaxSonar EZ1
#define PIN_SONAR1 7
//int pw_pin=7;
int arraysize = 9;
int array[] = { 0, 0, 0, 0, 0, 0, 0, 0, 0};
long inch;
int exact_cm_value;

// For CMD_GET_DIST_2 = 4
// HC-SR04
#define PIN_TRIG 8
#define PIN_ECHO 12
long dist2;

// For IR-lights and sensors = 5 and 6
#define IR_LED_L 9 // --> 220 Ohm (red-red-brown) --> long pin on LED
#define IR_LED_R 10 // --> 220 Ohm (red-red-brown) --> long pin on LED
#define IR_PIN_IN_L 3 // Digital read  
#define IR_PIN_IN_R 4 // Digital read 
#define IR_FREQ 38500  // IR frequency
#define IR_PULSE 20 // IR light pulse length, at least 15 msec, pref. 20 msec
int IRinpL;
int IRinpR;

void setup(){
   pinMode(PIN_LED, OUTPUT);
   pinMode(PIN_SONAR1, INPUT);
   pinMode(PIN_TRIG, OUTPUT);
   pinMode(PIN_ECHO, INPUT);
   pinMode(IR_LED_L, OUTPUT);
   pinMode(IR_LED_R, OUTPUT);
   pinMode(IR_PIN_IN_L, INPUT);
   pinMode(IR_PIN_IN_R, INPUT);

   // initialize i2c as slave
   Wire.begin(SLAVE_ADDRESS);

   // define callbacks for i2c communication
   Wire.onReceive(receiveData);
   Wire.onRequest(sendData);
}

void loop(){
   delay(DELAY_LOOP);
   GetTemp();
   GetDistance1();
   GetDistance2();
   GetIR();
}

// callback for received data
void receiveData(int byteCount){
   while(Wire.available()){
      cmdVal = Wire.read();
      if (cmdVal == 1){
         if (LEDstate == 0){
            digitalWrite(PIN_LED, HIGH); // set the LED on
            LEDstate = 1;
         } else{
            digitalWrite(PIN_LED, LOW); // set the LED off
            LEDstate = 0;
         }
         retVal = LEDstate;
      }
 
      if(cmdVal == 2){
         retVal = (int)temp;
      }

      if(cmdVal == 3){
         retVal = exact_cm_value;
      }

      if(cmdVal == 4){
         retVal = dist2;
      }

      if(cmdVal == 5){
         retVal = IRinpL;
      }

      if(cmdVal == 6){
         retVal = IRinpR;
      }
   }
}
 
// callback for sending data
void sendData(){
   Wire.write(retVal);
   retVal = 0;
}
 

void GetIR(void){
  // Left array
  tone(IR_LED_L, IR_FREQ, IR_PULSE);
  delay(2); //At least 2 msec, let the LED turn on
  IRinpL = digitalRead(IR_PIN_IN_L);

  delay(IR_PULSE); // Let the pulse in left die out before pulsing the right LED

  // Right array
  tone(IR_LED_R, IR_FREQ, IR_PULSE);
  delay(2); //At least 2 msec, let the LED turn on
  IRinpR = digitalRead(IR_PIN_IN_R);  
}

// Get the internal temperature of the arduino
void GetTemp(void){
   unsigned int wADC;
   double t;
   ADMUX = (_BV(REFS1) | _BV(REFS0) | _BV(MUX3));
   ADCSRA |= _BV(ADEN); // enable the ADC
   delay(20); // wait for voltages to become stable.
   ADCSRA |= _BV(ADSC); // Start the ADC
   while (bit_is_set(ADCSRA,ADSC));
   wADC = ADCW;
   temp = (wADC - 324.31 ) / 1.22;
}

void GetDistance1(void){
  for(int i = 0; i < arraysize; i++){
    inch = pulseIn(PIN_SONAR1, HIGH);
    array[i] = inch/58;
    delay(10);
  }
  array_arrangment(array,arraysize);
  exact_cm_value= filter(array,arraysize);
}

void GetDistance2(void){
   long duration;
   digitalWrite(PIN_TRIG, LOW);
   delayMicroseconds(2);
   digitalWrite(PIN_TRIG, HIGH);
   delayMicroseconds(10);
   digitalWrite(PIN_TRIG, LOW);
   duration = pulseIn(PIN_ECHO, HIGH);
   dist2 = (duration/2) / 29.1;
}

// ==== Helper functions for GetDistance1 ========
void array_arrangment(int *a,int n){
  //  Author: Bill Gentles, Nov. 12, 2010)
  for (int i = 1; i < n; ++i){
    int j = a[i];
    int k;
    for (k = i - 1; (k >= 0) && (j < a[k]); k--){
      a[k + 1] = a[k];
    }
    a[k + 1] = j;
  }
}

int filter(int *a,int n){
  int i = 0;
  int count = 0;
  int maxCount = 0;
  int filter = 0;
  int median;
  int prevCount = 0;
  while(i<(n-1)){
    prevCount=count;
    count=0;
    while(a[i]==a[i+1]){
      count++;
      i++;
    }
    if(count>prevCount && count>maxCount){
      filter=a[i];
      maxCount=count;
      median=0;
    }
    if(count==0){
      i++;
    }
    if(count==maxCount){//If the dataset has 2 or more modes.
      median=1;
    }
    if(filter==0||median==1){//Return the median if there is no mode.
      filter=a[(n/2)];
    }
    return filter;   
  } 
}

