from lamps import QLightST56EL
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ip_addr", help="IP address of lamp.", type=str)
    parser.add_argument("port", help="Port used by lamp", type=int)
    args = parser.parse_args()

    ip_addr = args.ip_addr
    port = args.port

if __name__=="__main__":
    main()