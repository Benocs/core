/// (C) 2014 by BENOCS GmbH. All rights reserved.

#include <cerrno>
#include <cstring>
#include <iostream>

#include <net/if.h>
#include <sys/ioctl.h>
#include <string.h>

int main(int argc, const char *const argv[])
{
    if ( argc < 2 )
    {
        std::cerr << "Usage: ifindex <interface name>\n";
    }
    else
    {
        ifreq req;
        std::strncpy(req.ifr_name, argv[1], sizeof(req.ifr_name));
        int fd = socket(AF_UNIX,SOCK_DGRAM,0);
        if ( fd < 0 )
        {
            std::cerr << "Error: Failed to create dummy socket: " << strerror(errno) << '\n';
            return 1;
        }
        else if ( ioctl(fd, SIOCGIFINDEX, &req) )
        {
            std::cerr << "Error: ioctl failed: " << strerror(errno) << '\n';
            return 1;
        }
        else
        {
            std::cout << req.ifr_ifindex << '\n';
        }
    }
}
