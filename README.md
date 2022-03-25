# fx-options-ukraine-war

(with Akos Török)

Did the FX options market expect the invasion announced on 02/24 04:06 UTC+1? The implied probability I estimate gives a hint:

![probability of invasion](./output/figures/prob-nonparam-thresh85.png "probability of invasion")

jump to [walkthrough](./walkthrough.ipynb) for results

## requirements
* required packages are in `requirements.txt`:

    ```bash
    python3 -m venv pyenv; source pyenv/bin/activate; pip install -r requirements.txt
    ```

* package [optools](https://github.com/ipozdeev/optools) must be downloaded where python can find it;

* environment variable `PROJECT_ROOT` must be set to the local repository;
