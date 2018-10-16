#include <EEPROM.h>

//###########################################################################################
//HCS301 Keeloq definitions
//###########################################################################################
//#define KEY_METHOD 0              // MUST BE 1 IF NORMAL KEY GEN METHOD TO BE USED
                                  // MUST BE 0 IF SIMPLE KEY GEN METHOD TO BE USED
                                  // (ENCRYPTION KEY= MANUFACTURER KEY)
// Key Method is currently selected from HMI Menu!                                  
                                  
#define HCS30X 1                  // MUST BE 1 IF PROGRAMMING HCS300-301,
                                  // MUST BE 0 IF PROGRAMMING HCS200
// MCODE: 0123456789ABCDEF    //Defined on LCD HMI 
//#define MCODE_0 0x0123            // LSWORD    
//#define MCODE_1 0x4567
//#define MCODE_2 0x89AB
//#define MCODE_3 0xCDEF            // MSWORD
#define SYNC 0X0000               // SYNCRONOUS COUNTER
//#define SEED_0 0x0000             // 2 WORD SEED VALUE   //Defined on LCD HMI
//#define SEED_1 0x0000
//#define SER_0 0x4567              // Serial Number LSB     //Defined on LCD HMI  
//#define SER_1 0x0123              // Serial Number MSB (MSbit will set 1 for Auto Shut off function) 
#define ENV_KEY 0x0000            // ENVELOPE KEY (NOT USED FOR HCS200)
#define AUTOFF 1                  // AUTO SHUT OFF TIMER ( NOT USED FOR HCS200)
//#define DISC70 0x00               // DISCRIMINATION BIT7-BIT0 Should be equal to 10 LSB of SN
//#define DISC8 0                   // DISCRIMINATION BIT8
//#define DISC9 0                   // DISCRIMINATION BIT9
#define DISC70 (SER_0 & 0x00FF)
#define DISC8 ((SER_0 & 0x0100)>>8)
#define DISC9 ((SER_0 & 0x0200)>>9)
#define OVR0 0                    // OVERFLOW BIT0 (DISC10 for HCS200)
#define OVR1 0                    // OVERFLOW BIT1(DISC11 for HCS200)
#define VLOW 1                    // LOW VOLTAGE TRIP POINT SELECT BIT (1=High voltage)
#define BSL0 0                    // BAUD RATE SELECT BIT0
#define BSL1 0                    // BAUD RATE SELECT BIT1(RESERVED for HCS200)
#define EENC 0                    // ENVELOPE ENCRYPTION SELECT(RESERVED for
                                  // HCS200)
#define DISEQSN 1                 // IF DISEQSN=1 SET DISCRIMINANT EQUAL TO
                                  // SERNUM BIT10-0 IF DISEQSN=0 SET DISCRIMINANT
                                  // AS defineD ABOVE

#define NUM_WRD 12                // NUMBER OF WORD TO PROGRAM INTO HCS
#define RES 0X0000                // RESERVED WORD
#define CONF_HI ((EENC<<7)|(BSL1<<6)|(BSL1<<5)|(VLOW<<4)|(OVR1<<3)|(OVR0<<2)|(DISC9<<1)|DISC8)
                                  
#define CLK 2               //(OUT PIN) Clock (S2) for Programming HCS //// White Wire
#define DATA 3              // (IN/OUT PIN) Data (PWM) for Programming HCS   //Blue Wire
#define HCSVDD 4            // (OUT PIN) HCS Vdd line      //Red Wire
#define PROG 5      // (IN PIN) Programming Key            //Program Key

// ****** HCS TIME PROGRAMMING EQUATE ********
#define Tps 4          // PROGRAM MODE SETUP TIME 4mS (3,5mS min, 4,5 max)
#define Tph1 4          // HOLD TIME 1 4mS (3,5mS min)
#define Tph2 62          // HOLD TIME 2 62uS (50uS min)
#define Tpbw 4          // BULK WRITE TIME 3mS (2,2mS min)
#define Tclkh 50          // CLOCK HIGH TIME 35uS (25uS min)
#define Tclkl 50          // CLOCK LOW TIME 35uS (25uS min)
#define Twc 50          // PROGRAM CYCLE TIME 40mS (36mS min)
word MCODE_0 = 0xCDEF;            // LSWORD    
word MCODE_1 = 0x89AB;
word MCODE_2 = 0x4567;
word MCODE_3 = 0x0123;            // MSWORD
word SEED_0 = 0x0000;             // 2 WORD SEED VALUE
word SEED_1 = 0x0000;
word SER_0 = 0x4567;              // Serial Number LSB
word SER_1 = 0x0123;              // Serial Number MSB (MSbit will set 1 for Auto Shut off function) 
boolean KEY_METHOD = 0;
word SER_0_Temp;                //Temp Serial Number copy for HMI Information
word SER_1_Temp;                //Temp Serial Number copy for HMI Information

//###########################################################################################
//SYSTEM VARIABLES
//###########################################################################################
char TempStringWord[5];
char TempStringDoubleByte[16];
word TempWord;
word Key[4];
word EEPROM_Write_Buffer[12];
word EEPROM_Read_Buffer[12];
boolean EEPROM_Write_Error = false;
boolean Button_State = false;

//############################################################################
//  EEPROM FUCNTIONS
//############################################################################
void EEPROMWriteFloat(int EEPROM_Address, float Float_Value) {
    uint8_t i=0;
    union UnionName {
        byte UnionByte[4];
        float UnionFloat;
    } ObjectName;
    ObjectName.UnionFloat=Float_Value;
 
    for (i=0; i<=3; i++, EEPROM_Address++)
    {
        EEPROM.write(EEPROM_Address,ObjectName.UnionByte[i]);
    }
}

float EEPROMReadFloat(int EEPROM_Address) {
    uint8_t i=0; 
    union UnionName {
        byte UnionByte[4];
        float UnionFloat;
    } ObjectName;   

    for (i=0; i<=3; i++, EEPROM_Address++)
    {
        ObjectName.UnionByte[i] = EEPROM.read(EEPROM_Address);
    }
    return ObjectName.UnionFloat;  
}

void EEPROMWriteInt(int EEPROM_Address, int Int_Value) {
    uint8_t i=0;
    union UnionName {
        byte UnionByte[4];
        int UnionInt;
    } ObjectName;
    ObjectName.UnionInt=Int_Value;
 
    for (i=0; i<=1; i++, EEPROM_Address++)
    {
        EEPROM.write(EEPROM_Address,ObjectName.UnionByte[i]);
    }
}

int EEPROMReadInt(int EEPROM_Address) {
    uint8_t i=0; 
    union UnionName {
        byte UnionByte[4];
        int UnionInt;
    } ObjectName;   

    for (i=0; i<=1; i++, EEPROM_Address++)
    {
        ObjectName.UnionByte[i] = EEPROM.read(EEPROM_Address);
    }
    return ObjectName.UnionInt;  
}

void ProgrammSimple() {
    int i=0;
    Key[i] = MCODE_0;  i++;
    Key[i] = MCODE_1;  i++;
    Key[i] = MCODE_2;  i++;
    Key[i] = MCODE_3;  i++;
  
    Serial.println("Encryption Key: ");
    for(int i=3; i>=0; i--){
        sprintf(TempStringWord, "%.4X", Key[i]);
        Serial.print(TempStringWord);
    }
    Serial.println("");
    delay(100);
    //Prepare EEPROM_Write_Buffer to write
    EEPROM_Write_Buffer[0]=Key[0];
    EEPROM_Write_Buffer[1]=Key[1];
    EEPROM_Write_Buffer[2]=Key[2];
    EEPROM_Write_Buffer[3]=Key[3];
    EEPROM_Write_Buffer[4]=SYNC;
    EEPROM_Write_Buffer[5]=0x0000;
    EEPROM_Write_Buffer[6]=SER_0;  //Serial Number Low Word
    EEPROM_Write_Buffer[7]=(SER_1 | (AUTOFF<<15));  //Serial Number High Byte + SET THE AUTO SHUT-OFF TIMER
    EEPROM_Write_Buffer[8]=SEED_0;
    EEPROM_Write_Buffer[9]=SEED_1;
    EEPROM_Write_Buffer[10]=ENV_KEY;
    EEPROM_Write_Buffer[11]=((CONF_HI<<8)|DISC70);
  
    Serial.println("EEPROM_Write_Buffer: ");
    for(int i=11; i>=0; i--){
        sprintf(TempStringWord, "%.4X", EEPROM_Write_Buffer[i]);
    Serial.print(TempStringWord); Serial.print(" ");
    }
    Serial.println("");
    Serial.println("Serial Number: ");
    sprintf(TempStringWord, "%.4X", EEPROM_Write_Buffer[7]);
    Serial.print(TempStringWord); Serial.print(" ");
    sprintf(TempStringWord, "%.4X", EEPROM_Write_Buffer[6]);
    Serial.print(TempStringWord); Serial.print(" ");
    //Serial.print(EEPROM_Write_Buffer[7],BIN);  Serial.print(EEPROM_Write_Buffer[6],BIN);
    Serial.println("");  
    Serial.println("EEPROM_Write_Buffer Config Word: ");
    sprintf(TempStringWord, "%.4X", EEPROM_Write_Buffer[11]);
    Serial.print("0x");Serial.print(TempStringWord); Serial.print(" ");
    Serial.println("");
    /*
    Serial.println("CONF_HI:");
    Serial.print(CONF_HI,BIN); 
    Serial.println("");  
    Serial.println("DISC70:");
    Serial.print(DISC70,BIN);
    Serial.println("");
    */

    
    //START M_PROG_INIT
    digitalWrite(DATA, LOW);
    digitalWrite(CLK, LOW);
    digitalWrite(HCSVDD, HIGH);
    delay(16); //delay 16milis
    //M_PROG_SETUP
    digitalWrite(CLK, HIGH);
    delay(Tps); //WAIT Program mode Setup Time (Tps)
    digitalWrite(DATA, HIGH);
    delay(Tph1);  //WAIT Program Hold Time 1 (Tph1)
    digitalWrite(DATA, LOW);
    delayMicroseconds(Tph2);     //WAIT Program Hold Time 2 (Tph2)
    //M_PROG_BULK_ER
    digitalWrite(CLK, LOW);
    delay(Tpbw);     //WAIT Program Bulk Write Time (Tpbw)
    
    Serial.println("Writting EEPROM...");
  
    for(int i=0; i<12; i++) { //One word at time
        for(int j=0; j<16; j++) {  //One bit at time
            digitalWrite(CLK, HIGH);
            if ( bitRead(EEPROM_Write_Buffer[i],j) ) { //Read bit from word
                digitalWrite(DATA, HIGH);
                } else {
                digitalWrite(DATA, LOW);
                }
            delayMicroseconds(Tclkh);   // Tclkh
            digitalWrite(CLK, LOW);
            delayMicroseconds(Tclkl);   // Tclkl
        } // One bit at time   
        digitalWrite(DATA, LOW);  //END OUTPUT WORD  DATA=0
        delay(Twc); //WAIT FOR WORD Write Cycle Time (Twc)
    } //One word at time
    //desligar linhas!
    Serial.println("Writting EEPROM Complete!");
    pinMode(DATA, INPUT);
}

boolean Verify_EEPROM()  { 
    Serial.println("Reading EEPROM...");

    for(int i=0; i<12; i++) { //One word at time
        EEPROM_Read_Buffer[i]=0xFFFF;  //Fill buffer with 0xFF
        for(int j=0; j<16; j++) {  //One bit at time
            delay(Twc); //WAIT FOR WORD Write Cycle Time (Twc)
            if(digitalRead(DATA)) {
                bitSet(EEPROM_Read_Buffer[i],j);
            }
            else {
                bitClear(EEPROM_Read_Buffer[i],j);        
            }
            digitalWrite(CLK, HIGH);
            delayMicroseconds(Tclkh);   // Tclkh
            digitalWrite(CLK, LOW);
            delayMicroseconds(Tclkl);   // Tclkl
        } // One bit at time   
    } //One word at time
    digitalWrite(HCSVDD, LOW); digitalWrite(CLK, LOW);
    pinMode(HCSVDD, INPUT); pinMode(CLK, INPUT); delay(100);
    //digitalWrite(HCSVDD, HIGH); digitalWrite(CLK, HIGH);
    Serial.println("EEPROM_Read_Buffer: ");
    for(int i=11; i>=0; i--){
        sprintf(TempStringWord, "%.4X", EEPROM_Read_Buffer[i]);
    Serial.print(TempStringWord); delay(50); Serial.print(" ");
    }
    Serial.println("");
    for(int i=0; i<12; i++) {
        if(EEPROM_Read_Buffer[i] != EEPROM_Write_Buffer[i]) EEPROM_Write_Error = true;
    }
    
    if(EEPROM_Write_Error){
        Serial.println("EEPROM Write Error!");
        EEPROM_Write_Error=false; 
        return false;
    }
    else {
        Serial.println("EEPROM Write Succefull!");   
        return true; 
    }     
     
}


void setup()
{
    Serial.begin(9600);
    pinMode(DATA, OUTPUT);      
    pinMode(CLK, OUTPUT);   
    pinMode(HCSVDD, OUTPUT);  
    pinMode(PROG, INPUT_PULLUP);  //Energia: pinMode(PROG, INPUT_PULLUP);
    digitalWrite(DATA, LOW);
    digitalWrite(CLK, LOW);
    digitalWrite(HCSVDD, LOW); 
    
    MCODE_0 = EEPROMReadInt(0);
    MCODE_1 = EEPROMReadInt(2);
    MCODE_2 = EEPROMReadInt(4);
    MCODE_3 = EEPROMReadInt(6);
    SER_0 = EEPROMReadInt(8);#pragma pack(1)

// This struct is based on table 3-2 from the HCS301 datasheet.
// https://www.mouser.com/datasheet/2/268/21143b-64900.pdf
// Configuration Word
struct ConfigWord
{
    unsigned int discrimination_bit_0:1;
    unsigned int discrimination_bit_1:1;
    unsigned int discrimination_bit_2:1;
    unsigned int discrimination_bit_3:1;
    unsigned int discrimination_bit_4:1;
    unsigned int discrimination_bit_5:1;
    unsigned int discrimination_bit_6:1;
    unsigned int discrimination_bit_7:1;
    unsigned int discrimination_bit_8:1;
    unsigned int discrimination_bit_9:1;

    unsigned int overflow_bit_0:1;
    unsigned int overflow_bit_1:1;
    
    unsigned int v_low_select:1;

    unsigned int baud_select_0:1;
    unsigned int baud_select_1:1;

    unsigned int reserved:1;
};

// This struct is based on tabel 3-1 from the HCS301 datasheet.
// https://www.mouser.com/datasheet/2/268/21143b-64900.pdf
// EEPROM Memory Map
struct EncoderData
{
    // Address word 0
    unsigned int key_0; // LSB
    unsigned int key_1;
    unsigned int key_2;
    unsigned int key_3; // MSB

    // Address word 4
    unsigned int sync = 0;

    // Address word 5
    unsigned int reserved_0 = 0;

    // Address word 6
    unsigned int serial_num_0; // LSB
    // serial_num_1 also contains a bit used to select the auto-shutoff timer
    unsigned int serial_num_1; // MSB

    // Address word 8
    unsigned int seed_0;
    unsigned int seed_1;

    // Address word 10
    unsigned int reserved_1 = 0;

    // Address word 11
    ConfigWord config_word;
};

const int DATA = 3; // This will be the data line.
const int CLOCK = 2; // This will be our clock.

// Timing constants for HCS 301. See figure 6-1 and table 6-1
// in datasheet for more info.
const int TPS = 4; // ms
const int TPH1 = 4; // ms
const int TPH2 = 60; // us
const int TPBW = 4; // ms
const int TCLKH = 50; // us - min of 50 us
const int TCLKL = 50; // us - min of 50 us
const int TWC = 52; // ms
const int TDV = 35; // us

EncoderData programming_data;

// the setup routine runs once when you press reset:
void setup() {
  // setup pins
  pinMode(DATA, OUTPUT);
  pinMode(CLOCK, OUTPUT);
  
  // setup data to send to the HCS301

  // This is just random. Should probably use the KEELOQ algorithm.
  // See section 3.1 of the HCS301 datasheet for more information.
  programming_data.key_0 = 0x3C5F;
  programming_data.key_1 = 0x8404;
  programming_data.key_2 = 0xFFFF;
  programming_data.key_3 = 0xFFFF;

  // Serial info is just made up but the most significant bit is set
  // high to turn on the auto-shutoff timer.
  programming_data.serial_num_0 = 0xFFFF;
  programming_data.serial_num_1 = 0xFFFF;

  programming_data.seed_0 = 0xFFFF;
  programming_data.seed_1 = 0xFFFF;

  // Discrimination bits are normally set to the 10 least significant
  // bits of the serial number.
  programming_data.config_word.discrimination_bit_0 = 1;
  programming_data.config_word.discrimination_bit_1 = 1;
  programming_data.config_word.discrimination_bit_2 = 1;
  programming_data.config_word.discrimination_bit_3 = 1;
  programming_data.config_word.discrimination_bit_4 = 1;
  programming_data.config_word.discrimination_bit_5 = 1;
  programming_data.config_word.discrimination_bit_6 = 1;
  programming_data.config_word.discrimination_bit_7 = 1;
  programming_data.config_word.discrimination_bit_8 = 1;
  programming_data.config_word.discrimination_bit_9 = 1;

  programming_data.config_word.overflow_bit_0 = 0;
  programming_data.config_word.overflow_bit_1 = 0;

  programming_data.config_word.v_low_select = 0; // 1 = 9-12V, 0 = 6V

  // This sets the basic pulse element to 400 micro seconds.
  // See section 3.6.3 of the HCS301 datasheet for more info.
  programming_data.config_word.baud_select_0 = 0;
  programming_data.config_word.baud_select_1 = 0;

  // Reserved bit, set to 0
  programming_data.config_word.reserved = 0;
  
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  Serial.println("Hello world");
}


// the loop routine runs over and over again forever:
void loop() {
  // Set device into programming mode
  digitalWrite(CLOCK, HIGH);
  delay(TPS);
  digitalWrite(DATA, HIGH);
  delay(TPH1);
  digitalWrite(DATA, LOW);
  delayMicroseconds(TPH2);
  digitalWrite(CLOCK, LOW);
  delay(TPBW);

  word input_array[sizeof(programming_data)/2];
  memcpy(input_array, &programming_data, sizeof(programming_data));
  word current_word;
  uint8_t data_value;
  for (int n = 0; n < sizeof(programming_data)/2; n++)
  {
    current_word = input_array[n];
    for (int bit_index = 0; bit_index < 16 ; bit_index++)
    {
      data_value = bitRead(current_word, bit_index);
      digitalWrite(DATA, data_value);
      digitalWrite(CLOCK, HIGH);
      delayMicroseconds(TCLKH);
      digitalWrite(CLOCK, LOW);
      delayMicroseconds(TCLKL);
    }

    digitalWrite(DATA, LOW);

    delay(TWC);
  }

  // Begin verify operation
  pinMode(DATA, INPUT);

  EncoderData returnedData;
  word returned_array[sizeof(returnedData)/2];
  int bit_value;

  for (int i = 0; i < sizeof(returnedData)/2; i++)
  {
    current_word = 0;
    for (int bit_index = 0; bit_index < 16; bit_index++)
    {
      bit_value = digitalRead(DATA);
      digitalWrite(CLOCK, HIGH);
      delayMicroseconds(TDV);
      current_word = current_word | (bit_value << bit_index);
      delayMicroseconds(TCLKH); // subtract TDV to get 50% duty cycle
      digitalWrite(CLOCK, LOW);
      delayMicroseconds(TCLKL);
    }

    returned_array[i] = current_word;
  }

  memcpy(&returnedData, returned_array, sizeof(returnedData));

  bool passed = true;
  for (int i = 0; i < 12; i++)
  {
    if (input_array[i] != returned_array[i])
    {
      passed = false;
      Serial.println("Word [%d] differs: ");
      Serial.print("    sent: 0x");
      Serial.println(input_array[i], HEX);
      Serial.print("    recd: 0x");
      Serial.println(returned_array[i], HEX);
    }
  }

  if (passed)
      Serial.println("Succeeded");

  // Don't do anything else.
  while(1);
}
    SER_1 = EEPROMReadInt(10);
    SEED_0 =  EEPROMReadInt(12);
    SEED_1 =  EEPROMReadInt(14);
    KEY_METHOD = EEPROM.read(16);
    
    delay(3000);
  
}

int k = 1;
void loop()
{
    if (k == 1) {
        k = 2;
        ProgrammSimple();
    }
    else if (k == 2) {
        k = 3;
        Verify_EEPROM();
    }
}