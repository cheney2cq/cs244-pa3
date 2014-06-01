/*
 * Client will connect to the server on port 5000 and send 8 KB blocks with
 * timestamps at the beginning and end of the block. The beginning timestamp
 * is unused now; the end timestamp signifies the time the entire 8 KB block
 * was accepted by the TCP stack for transmission.
 *
 * Written by CJ Cullen and Stephen Barber for CS 244 at Stanford, Spring 2014
 *
 */
#include <errno.h>
#include <error.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/types.h>

#define BUF_SIZE 8192
#define TIME_SECS 100
#define SNDBUF_SIZE_KB 200

int main(int argc, char *argv[]) {
    if (argc < 2) {
        error(1, 0, "dest IP is required");
    }

    int sockfd = socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK, 0);
    if (sockfd == -1)
        error(1, errno, "could not create socket");

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(5000);
    int ret = inet_pton(AF_INET, argv[1], &addr.sin_addr.s_addr);
    if (ret != 1)
        error(1, errno, "could not read IP address \"%s\"", argv[1]);

    ret = connect(sockfd, (struct sockaddr *)&addr, sizeof addr);

    /* Sleep time between timestamps */
    struct timespec sleep_time;
    sleep_time.tv_sec = 0;
    sleep_time.tv_nsec = 10000;

    struct timeval finish_time;
    gettimeofday(&finish_time, NULL);

    finish_time.tv_sec += TIME_SECS;

    int sendbuff = SNDBUF_SIZE_KB * 1024;
    ret = setsockopt(sockfd, SOL_SOCKET, SO_SNDBUF, &sendbuff, sizeof(sendbuff));
    if (ret) {
        error(1, errno, "could not set sockopt SO_SNDBUF");
    }

    while (1) {
        struct timeval now;
        size_t tv_size = sizeof now;
        unsigned char buf[BUF_SIZE];
        int total_bytes_sent = 0;

        gettimeofday(&now, NULL);
        memcpy(buf, &now, tv_size);

        while (total_bytes_sent < BUF_SIZE - tv_size) {
            int bytes_sent = write(sockfd, buf + total_bytes_sent, BUF_SIZE - total_bytes_sent - tv_size);

            if (bytes_sent == -1)
                if (errno == EAGAIN || errno == EWOULDBLOCK) {
                    nanosleep(&sleep_time, NULL);
                    if (total_bytes_sent == 0) {
                        gettimeofday(&now, NULL);
                        memcpy(buf, &now, tv_size);
                    }
                    continue;
                }
                else
                    error(1, errno, "failed to write to socket");

            total_bytes_sent += bytes_sent;
        }
        total_bytes_sent = 0;

        gettimeofday(&now, NULL);

        while (total_bytes_sent < tv_size) {
            int bytes_sent = write(sockfd, (unsigned char *)&now + total_bytes_sent, tv_size - total_bytes_sent);

            if (bytes_sent == -1)
                if (errno == EAGAIN || errno == EWOULDBLOCK) {
                    nanosleep(&sleep_time, NULL);
                    if (total_bytes_sent == 0)
                        gettimeofday(&now, NULL);
                    continue;
                }
                else
                    error(1, errno, "failed to write to socket");

            total_bytes_sent += bytes_sent;
        }


        if (timercmp(&now, &finish_time, >))
            return 0;
        nanosleep(&sleep_time, NULL);
    }

    return 0;
}
