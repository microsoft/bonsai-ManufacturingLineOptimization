'''
A set of tests to insure that line configuration makes sense

(1) connectivity of the line (2) existance of at least one source and one sink (3) no dangling machine/conveyor  

'''
import os 
import pytest
# from pathlib import Path
# p= Path(os.getcwd())
# os.chdir(p.parent)
from line_config import adj, con_balance, con_join 

def test_adj_format():
    assert type(adj) == dict
    for machine in adj.keys():
        assert type(adj[machine]) == tuple 

def test_line_con_format():
    assert type(con_balance) == list
    if con_balance:
        assert type(con_balance[0]) == tuple

def test_line_con_join():
    assert type(con_join) == list
    if con_join:
        assert type(con_join[0]) == tuple

def test_adj_machine_name_unique():
    
    

