#include <string>

#define RF24_PA_MIN 0
#define RF24_PA_LOW 1
#define RF24_PA_HIGH 2
#define RF24_PA_MAX 3

#define RF24_250KBPS 0
#define RF24_1MBPS 1
#define RF24_2MBPS 2

class RF24 {
    public:
    RF24(int p, int q);
    void begin();
    void powerUp();
    void powerDown();
    void startListening();
    void stopListening();
    void setPALevel(int pa_level);
    void setChannel(int channel);
    void setDataRate(int data_rate);
    void openWritingPipe(long int pipe);
    void openReadingPipe(int i, long int pipe);
    void enableDynamicPayloads();
    void read(char* msg, unsigned long msg_size);
    void write(const char msg[], unsigned long msg_size);
    bool available();

    std::string command;

    private:
    bool msg_available;
    int pa_level;
    int channel;
    int data_rate;
    long int reading_pipe;
    long int writing_pipe;
};