__version__ = "0.0.1"
from functools import update_wrapper


class LazyProperty(property):
    def __init__(self, method, fget=None, fset=None, fdel=None, doc=None):
        """
        Create an instance of a ``LazyProperty`` (or ``LazyWritableProperty``) inside a class ``C``'s declaration,
        this instance will be a class variable, just like a normal descriptor. You can access it by
        ``C.<method_name>``.

        :param method: The method which you want to cache. This is different from ``property`` which only takes
            *fget*, *fset*, *fdel* and *doc*. It is because that ``property`` already assumes that you
            have a hidden attribute ``_x`` and some ``getx`` and ``setx`` methods. But now you have to
            create it by yourself.
        :param fget: Usually ``None``.
        :param fset: For a ``LazyProperty`` instance, a ``__set__`` method inherits from ``property.__set__``.
            Thus it will directly call that ``__set__``. Since the default *fset* is ``None``,
            the ``property.__set__`` method will raise an ``AttributeError``. But for a ``LazyWritableProperty``,
            this will not happen since a ``__set__`` method is given and overrides the ``property.__set__`` method.
        :param fdel: Usually ``None``.
        :param doc: It will get the *method*s documentation if it is given.
        """

        self.method = method
        self.cache_name = "_{}".format(self.method.__name__)

        doc = doc or method.__doc__
        super(LazyProperty, self).__init__(fget=fget, fset=fset, fdel=fdel, doc=doc)
        # Transfer attribute from *method*.
        update_wrapper(self, method)

    def __get__(self, instance, owner):
        """
        Overrides ``__get__`` method inherits from ``property``.
        Once you get an attribute in the instance with ``self.method.__name__``,
        it will add ``self.cache_name`` into ``instance.__dict__``, then next time you
        try to get it, it will directly get ``instance.__dict__[self.cache_name]``. That is how
        it works.

        :param instance: The instance of the class ``c`` where this ``LazyProperty`` is declared.
        :param owner: The class ``C`` where this ``LazyProperty`` is declared.
        :return: The result calculated by ``self.method(instance)`` or by ``self.fget(instance)``.
        """

        if instance is None:
            # If you call from class of the instance ``c``, e.g., ``C.<method_name>``, you will
            # get a ``LazyProperty`` instance.
            return self

        if hasattr(instance, self.cache_name):
            # Second time you call a property decorated, it will find ``_<method_name>`` in ``instance.__dict__``.
            result = getattr(instance, self.cache_name)
        else:
            if self.fget is not None:
                # Usually not used.
                result = self.fget(instance)
            else:
                result = self.method(instance)
            # First time you call a property decorated, this value is set in the *instance*.
            setattr(instance, self.cache_name, result)

        return result


class LazyWritableProperty(LazyProperty):
    def __set__(self, instance, value):
        """
        If you add this method directly into the definition of ``LazyProperty``, then you cannot
        make a read-only property by it.

        :param instance: The instance of the class where this ``LazyProperty`` is declared.
        :param value: The value you want to set for ``instance.__dict__[self.cache_name]``.
        :return: No return.
        """
        if instance is None:
            raise AttributeError

        if self.fset is None:
            setattr(instance, self.cache_name, value)
        else:
            self.fset(instance, value)
