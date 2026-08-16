import argparse

from app.agent import print_decision, reconcile

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sku", default="SKU-1002")
    args = parser.parse_args()

    print("LEC AI inventory reconciliation demo")
    decision = reconcile(args.sku)
    print_decision(decision)
