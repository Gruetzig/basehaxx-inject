#include <stdio.h>
#include <stdlib.h>

#define CRC_POLY 0x1021

unsigned short ccitt16(unsigned char *data, unsigned int length)
{
    unsigned short crc = 0xFFFF;

    for (unsigned int i = 0; i < length; i++)
    {
        crc ^= (unsigned short)data[i] << 8;

        for (int j = 0; j < 8; j++)
            if (crc & 0x8000)
                crc = crc << 1 ^ CRC_POLY;
            else
                crc = crc << 1;
    }

    return crc;
}

int main(int argc, char** argv) {
    if (argc != 2) {
        perror("Invalid number of arguments: %d\nUsage: orashashfixer <save>\n");
    }
    FILE *file = fopen(argv[1], "rb");
    if (file == NULL) {
        perror("file doesn't exist D: \n");
        return 1;
    }
    fseek(file, 0, SEEK_END);
    long size = ftell(file);
    printf("File size: %ld\n", size);
    fseek(file, 0, SEEK_SET);
    void *buf = malloc(size);
    fread(buf, 1, size, file);

    unsigned short ccitt = ccitt16(buf + 0x23a00, 0x7ad0);
    *(unsigned short*)(buf + 0x75fca) = ccitt;

    ccitt = ccitt16(buf + 0x67c00, 0xe058);
    *(unsigned short*)(buf + 0x75fe2) = ccitt;
    fclose(file);
    file = fopen(argv[1], "wb");
    fwrite(buf, 1, size, file);
    fclose(file);
    return 0;
}