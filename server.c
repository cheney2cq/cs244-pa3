#include <errno.h>
#include <error.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/types.h>

#define BUF_SIZE 8192
#define RCVBUF_SIZE_KB 30

int main(int argc, char *argv[]) {
    if (argc < 2) {
        error(1, 0, "logfile is required");
    }

    FILE *logfile = fopen(argv[1], "w");
    if (!logfile)
        error(1, errno, "could not open logfile");

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd == -1)
        error(1, errno, "could not create socket");
    struct sockaddr_in bindaddr;
    bindaddr.sin_family = AF_INET;
    bindaddr.sin_port = htons(5000);
    bindaddr.sin_addr.s_addr = htonl(0);

    int ret = bind(sockfd, (struct sockaddr *)&bindaddr, sizeof bindaddr);

    if (ret == -1)
        error(1, errno, "could not bind socket");

    ret = listen(sockfd, 0);
    if (ret == -1)
        error(1, errno, "could not mark socket as passive");

    /* Loop forever */
    int connfd;
    struct sockaddr connaddr;
    socklen_t addrlen;
    while ((connfd = accept(sockfd, &connaddr, &addrlen)) != -1) {
        int recvbuf = RCVBUF_SIZE_KB * 1024;
        ret = setsockopt(connfd, SOL_SOCKET, SO_RCVBUF, &recvbuf, sizeof(recvbuf));
        if (ret) {
            error(1, errno, "could not set sockopt SO_RCVBUF");
        }

        while (1) {
            struct timeval block_start, block_end;
            size_t tv_size = sizeof block_start;
            unsigned char buf[BUF_SIZE];
            int total_bytes_read = 0;

            struct timeval now;

            while (total_bytes_read < BUF_SIZE) {
                int bytes_read = read(connfd, buf + total_bytes_read, BUF_SIZE - total_bytes_read);

                if (bytes_read == -1)
                    error(1, errno, "failed to read from socket");

                total_bytes_read += bytes_read;
            }
            gettimeofday(&now, NULL);

            memcpy(&block_start, buf, tv_size);
            memcpy(&block_end, buf + BUF_SIZE - tv_size, tv_size);

            struct timeval tv_diff, block_diff;
            //timersub(&block_start, &block_end, &block_diff);
            timersub(&now, &block_end, &tv_diff);

            fprintf(logfile, "%ld\n", tv_diff.tv_sec * 1000 + tv_diff.tv_usec / 1000);
            fflush(logfile);
        }
    }
    error(1, errno, "accept failed");

    return 0;
}
