def hide_module_model_and_layer_methods():
  """Hide methods and properties defined in the base classes of Keras layers.

  We hide all methods and properties of the base classes, except:
  - `__init__` is always documented.
  - `call` is always documented, as it can carry important information for
    complex layers.
  """
  module_contents = list(tf.Module.__dict__.items())
  model_contents = list(tf_keras.Model.__dict__.items())
  layer_contents = list(tf_keras.layers.Layer.__dict__.items())

  for name, obj in module_contents + layer_contents + model_contents:
    if name == '__init__':
      # Always document __init__.
      continue

    if name == 'call':
      # Always document `call`.
      if hasattr(obj, doc_controls._FOR_SUBCLASS_IMPLEMENTERS):  # pylint: disable=protected-access
        delattr(obj, doc_controls._FOR_SUBCLASS_IMPLEMENTERS)  # pylint: disable=protected-access
      continue

    # Otherwise, exclude from documentation.
    if isinstance(obj, property):
      obj = obj.fget

    if isinstance(obj, (staticmethod, classmethod)):
      obj = obj.__func__

    try:
      doc_controls.do_not_doc_in_subclasses(obj)
    except AttributeError:
      pass