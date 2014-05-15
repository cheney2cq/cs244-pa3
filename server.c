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

/* http://stackoverflow.com/questions/1858050/how-do-i-compare-two-timestamps-in-c */
int timeval_subtract (struct timeval *result, struct timeval *x, struct timeval *y) {
     /* Perform the carry for the later subtraction by updating y. */
     if (x->tv_usec < y->tv_usec) {
         int nsec = (y->tv_usec - x->tv_usec) / 1000000 + 1;
         y->tv_usec -= 1000000 * nsec;
         y->tv_sec += nsec;
     }
     if (x->tv_usec - y->tv_usec > 1000000) {
         int nsec = (x->tv_usec - y->tv_usec) / 1000000;
         y->tv_usec += 1000000 * nsec;
         y->tv_sec -= nsec;
     }

     /* Compute the time remaining to wait.
        tv_usec is certainly positive. */
     result->tv_sec = x->tv_sec - y->tv_sec;
     result->tv_usec = x->tv_usec - y->tv_usec;

     /* Return 1 if result is negative. */
     return x->tv_sec < y->tv_sec;
}

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
        while (1) {
            struct timeval tv;
            size_t tv_size = sizeof tv;
            unsigned char buf[BUF_SIZE];
            int total_bytes_read = 0;

            while (total_bytes_read < BUF_SIZE) {
                int bytes_read = read(connfd, buf + total_bytes_read, BUF_SIZE - total_bytes_read);

                if (bytes_read == -1)
                    error(1, errno, "failed to read from socket");

                total_bytes_read += bytes_read;
            }

            struct timeval now;
            gettimeofday(&now, NULL);

            memcpy(&tv, buf, tv_size);

            struct timeval tv_diff;
            timersub(&now, &tv, &tv_diff);

            fprintf(logfile, "%ld\n", tv_diff.tv_sec * 1000 + tv_diff.tv_usec / 1000);
            fflush(logfile);
        }
    }
    error(1, errno, "accept failed");

    return 0;
}
