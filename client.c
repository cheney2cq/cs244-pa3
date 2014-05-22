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
    sleep_time.tv_nsec = 1000;

    struct timeval finish_time;
    gettimeofday(&finish_time, NULL);

    finish_time.tv_sec += 100;

    int sendbuff = 200 * 1024;
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

        while (total_bytes_sent < BUF_SIZE) {
            int bytes_sent = write(sockfd, buf + total_bytes_sent, BUF_SIZE - total_bytes_sent);

            if (bytes_sent == -1)
                if (errno == EAGAIN || errno == EWOULDBLOCK) {
                    nanosleep(&sleep_time, NULL);
                    continue;
                }
                else
                    error(1, errno, "failed to write to socket");

            total_bytes_sent += bytes_sent;
        }
	total_bytes_sent = 0;

//        while (total_bytes_sent < tv_size) {
//            int bytes_sent = write(sockfd, buf + total_bytes_sent, tv_size - total_bytes_sent);
//
//            if (bytes_sent == -1)
//                if (errno == EAGAIN || errno == EWOULDBLOCK) {
//                    nanosleep(&sleep_time, NULL);
//                    continue;
//                }
//                else
//                    error(1, errno, "failed to write to socket");
//
//            total_bytes_sent += bytes_sent;
//        }
//

        if (timercmp(&now, &finish_time, >))
            return 0;
        nanosleep(&sleep_time, NULL);
    }

    return 0;
}
