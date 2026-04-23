def _get_message(self) -> str:
        return """
You are calling `st.pyplot()` without any arguments. After December 1st, 2020,
we will remove the ability to do this as it requires the use of Matplotlib's global
figure object, which is not thread-safe.

To future-proof this code, you should pass in a figure as shown below:

```python
>>> fig, ax = plt.subplots()
>>> ax.scatter([1, 2, 3], [1, 2, 3])
>>>    ... other plotting actions ...
>>> st.pyplot(fig)
```
"""